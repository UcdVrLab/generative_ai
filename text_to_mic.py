
import pyttsx3

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def main():
    while True:
        text = input("Paste your text here (Press Enter to speak, or type 'exit' to quit): ")
        
        if text.lower() == 'exit':
            print("Exiting...")
            break
        
        if text.strip():  # Check if the input text is not empty
            text_to_speech(text)
        else:
            print("No text entered. Please paste some text to speak.")

if __name__ == "__main__":
    print("Text-to-Speech Program")
    print("----------------------")
    main()
