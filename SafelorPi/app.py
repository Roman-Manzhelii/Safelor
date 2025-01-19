import os
import sys
import time
import asyncio
import threading
from worker_compliance_handler import WorkerComplianceHandler
from sensors.pir import PIRSensor, monitor_pir, wait_for_entry_and_exit
from sensors.rfid import RFIDScanner
from sensors.traffic_light import TrafficLight
from sensors.speaker import Speaker
from sensors.camera import Camera
from multiprocessing import Value, Event

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

ZONE_ID = 1

async def main():
    compliance_handler = WorkerComplianceHandler()
    compliance_handler.start_zone_online_update(zone_id=ZONE_ID)
    pir1 = PIRSensor(pin=11)
    pir2 = PIRSensor(pin=13)
    rfid_scanner = RFIDScanner()
    traffic_light = TrafficLight()
    speaker = Speaker()
    camera = Camera()

    HZoneEntered = Value('i', -1)  # -1 means undefined
    premature_exit = Event()
    stop_monitoring = Event()

    try:
        print("System starting...")
        current_requirements = await compliance_handler.request_zone_requirements(zone_id=ZONE_ID)

        if current_requirements:
            print(f"Initial zone requirements: {current_requirements}")
        else:
            print("No zone requirements found at startup.")

        while True:
            print("System in sleep mode.")
            HZoneEntered.value = -1
            premature_exit.clear()
            stop_monitoring.clear()

            emp_identified = False
            ppe_missing = set()
            scan_image_name = None
            scan_image_id = None
            boots_scanned = False

            current_requirements = compliance_handler.get_current_zone_requirements()

            if current_requirements:
                print(f"Current zone requirements: {current_requirements}")
            else:
                print("No current zone requirements available.")

            while not pir1.is_triggered():
                time.sleep(0.1)

            pir_thread = threading.Thread(
            target=monitor_pir,
            args=(pir1, pir2, HZoneEntered, premature_exit, stop_monitoring),
            daemon=True
            )
            pir_thread.start()

            scan_image_name_initial = await camera.capture_image()
            scan_image_id_initial = await asyncio.gather(
                compliance_handler.upload_image_and_get_id(scan_image_name_initial),
                flash_and_set_red(traffic_light),
                speaker.play_audio("ppe_scan_started")
            )

            if premature_exit.is_set():
                    await handle_premature_exit(
                        compliance_handler, speaker, rfid_scanner, traffic_light,
                        scan_image_id_initial=scan_image_id_initial[0],
                        scan_image_id=scan_image_id, emp_identified=emp_identified,
                        ppe_missing=ppe_missing, HZoneEntered=HZoneEntered,
                        stop_monitoring=stop_monitoring, pir_thread=pir_thread,
                        boots_scanned=boots_scanned, current_requirements=current_requirements
                    )
                    continue
            
            current_requirements = compliance_handler.get_current_zone_requirements()
            scan_image_id_initial = scan_image_id_initial[0]

            if 1 not in current_requirements and 2 not in current_requirements:
                await speaker.play_audio("helmet_and_vest_not_required")
            else:
                for _ in range(3):
                    if premature_exit.is_set():
                        break

                    ppe_missing.clear()
                    await speaker.play_audio("look_straight_at_the_camera")
                    await asyncio.sleep(2)

                    if premature_exit.is_set():
                        break
                    
                    scan_image_name = await camera.capture_image()
                    await speaker.play_audio("snapshot_taken_starting_analysis")
                    ppe_missing_result, emp_identified, scan_image_id = await compliance_handler.analyze_worker_and_ppe(
                        scan_image_name, speaker, premature_exit, zone_id=1
                    )
                    ppe_missing.update(ppe_missing_result)


                    if emp_identified:
                        break

                    if premature_exit.is_set():
                        break

                    await speaker.play_audio("face_not_detected")

                if premature_exit.is_set():
                    await handle_premature_exit(
                        compliance_handler, speaker, rfid_scanner, traffic_light,
                        scan_image_id_initial=scan_image_id_initial,
                        scan_image_id=scan_image_id, emp_identified=emp_identified,
                        ppe_missing=ppe_missing, HZoneEntered=HZoneEntered,
                        stop_monitoring=stop_monitoring, pir_thread=pir_thread,
                        boots_scanned=boots_scanned, current_requirements=current_requirements
                    )
                    continue

                await speaker.play_audio("image_analysis_completed")

            current_requirements = compliance_handler.get_current_zone_requirements()

            if premature_exit.is_set():
                    await handle_premature_exit(
                        compliance_handler, speaker, rfid_scanner, traffic_light,
                        scan_image_id_initial=scan_image_id_initial,
                        scan_image_id=scan_image_id, emp_identified=emp_identified,
                        ppe_missing=ppe_missing, HZoneEntered=HZoneEntered,
                        stop_monitoring=stop_monitoring, pir_thread=pir_thread,
                        boots_scanned=boots_scanned, current_requirements=current_requirements
                    )
                    continue
            
            if not 3 in current_requirements:
                await speaker.play_audio("boot_scan_not_required")
            else:
                for _ in range(3):
                    if premature_exit.is_set():
                        break

                    rfid_scanner.reset()
                    await speaker.play_audio("please_scan_your_boots")
                    traffic_light.set_yellow()
                    boots_scanned = await rfid_scanner.scan()
                    if boots_scanned:
                        await speaker.play_audio("boots_scanned")
                        break


                if not boots_scanned or rfid_scanner.cleaned:
                    await speaker.play_audio("boots_not_scanned")
                    ppe_missing.add(3)

            ppe_missing = {ppe_id for ppe_id in ppe_missing if ppe_id in current_requirements}

            if premature_exit.is_set():
                await handle_premature_exit(
                    compliance_handler, speaker, rfid_scanner, traffic_light,
                    scan_image_id_initial=scan_image_id_initial,
                    scan_image_id=scan_image_id, emp_identified=emp_identified,
                    ppe_missing=ppe_missing, HZoneEntered=HZoneEntered,
                    stop_monitoring=stop_monitoring, pir_thread=pir_thread,
                    boots_scanned=boots_scanned, current_requirements=current_requirements
                )
                continue

            if ppe_missing:
                traffic_light.set_red()
                await speaker.play_audio("please_return_with_correct_ppe")
            else:
                traffic_light.set_green()
                await speaker.play_audio("please_proceed")

            stop_monitoring.set()
            pir_thread.join()

            await wait_for_entry_and_exit(pir1, pir2, speaker, HZoneEntered)
            traffic_light.turn_off_all()

            compliance_handler.send_result(scan_image_id_initial, scan_image_id, emp_identified, ppe_missing, HZoneEntered, current_requirements)
            rfid_scanner.cleanup()
            print("System returning to sleep mode.")

    except KeyboardInterrupt:
        cleanup(pir1, pir2, traffic_light, rfid_scanner)
        compliance_handler.stop_zone_updates()
        compliance_handler.close_connections()

async def handle_premature_exit(
    compliance_handler, speaker, rfid_scanner, traffic_light, 
    scan_image_id_initial=None, scan_image_id=None, emp_identified=None,
    ppe_missing=None, HZoneEntered=None, stop_monitoring=None, pir_thread=None, 
    boots_scanned=None, current_requirements=None
):
    print("--- Premature Exit Detected ---")
    if not emp_identified and 1 in current_requirements:
        ppe_missing.add(1)
    if not emp_identified and 2 in current_requirements:
        ppe_missing.add(2)
    if not boots_scanned and 3 in current_requirements:
        ppe_missing.add(3)

    compliance_handler.send_result(scan_image_id_initial, scan_image_id, emp_identified, ppe_missing, HZoneEntered, current_requirements)
    if HZoneEntered.value == 1:
        await speaker.play_audio("entering_hazard_zone")
    else:
        await speaker.play_audio("exiting_hazard_zone")
    traffic_light.turn_off_all()

    if rfid_scanner:
        rfid_scanner.cleanup()

    stop_monitoring.set()
    pir_thread.join()

def cleanup(pir1, pir2, traffic_light, rfid_scanner):
    pir1.cleanup()
    pir2.cleanup()
    traffic_light.cleanup()

    if rfid_scanner:
        rfid_scanner.cleanup()

async def flash_and_set_red(traffic_light):
    await traffic_light.flash_colors()
    traffic_light.set_red()

if __name__ == "__main__":
    asyncio.run(main())