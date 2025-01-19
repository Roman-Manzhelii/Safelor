from pubnub.callbacks import SubscribeCallback


class PubNubListener(SubscribeCallback):
    def __init__(self, handlers):
        super().__init__()
        self.handlers = handlers
        
    def status(self, pubnub, status):
        if status.is_error():
            print(f"Status error: {status.category}")
        else:
            print(f"Connected with status: {status.category}")

    
    def message(self, pubnub, message):
        channel_name = message.channel
        message_content = message.message
        publisher = message.publisher
        print(f"Received message on channel '{channel_name}': {message_content}")
        print(f"Message published by: {publisher}")
        #use passed in handlers to handle appropriate messages
        if channel_name in self.handlers:
            self.handlers[channel_name](message_content)
        else:
            print(f"No handler defined for channel '{channel_name}'")

