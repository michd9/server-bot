#!/usr/bin/env python

import os
import telebot
from telebot import types
import subprocess
import time
import board
import adafruit_dht
import psutil
from decouple import config

# Load environment variables
TOKEN = config('TOKEN')

print("Initialization...")

# Replace 'YOUR_API_TOKEN' with your actual Telegram Bot API token
bot = telebot.TeleBot(TOKEN)
dhtDevice = adafruit_dht.DHT22(board.D4)

@bot.message_handler(commands=['start', 'help'])
def handle_start_message(message):
    response = (
        "Welcome to the Bot!\n"
        "Available commands:\n"
        "/start or /help - Show this help message\n"
        "/Hi - Say hi\n"
        "/Pic - Capture and send a picture\n"
        "/Data - Get sensor data (temperature and humidity)\n"
        "/Stat - Get the machine CPU temperature\n"
        "/Reboot - Get CPU temperature status\n"
        "/Poweroff - Reboot the Raspberry Pi"
    )
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text == 'Hi')
def handle_hello_message(message):
    print("Replying to Hi.")
    bot.reply_to(message, 'Hello')

@bot.message_handler(func=lambda message: message.text == 'Pic')
def handle_picture_message(message):
    # Capture an image using fswebcam
    print("Replying to Pic.")
    subprocess.run(['fswebcam', '-r 1280x1024','webcam_image.jpg'])

    # Send the image as a photo to the user
    with open('webcam_image.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)

@bot.message_handler(func=lambda message: message.text == 'Data')
def handle_data_message(message):

    print("Replying to Data.")

    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity
        print(
            "Temp: {:.1f} C    Humidity: {}% ".format(
                temperature_c, humidity
            )
        )

        # Read data from DHT22 sensor
        # humidity, temperature = adafruit_dht.read_retry(adafruit_dht.DHT22, 4)

        # Check if data reading was successful
        if humidity is not None and temperature_c is not None:
            response = f'Temperature: {temperature_c:.1f}°C\nHumidity: {humidity:.1f}%'
        else:
            response = 'Failed to retrieve sensor data.'

        # Send the sensor data as a reply
        bot.reply_to(message, response)

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        response = error.args[0]
        print(response)
        bot.reply_to(message, response)
        time.sleep(2.0)
    except Exception as error:
        response = error.args[0]
        print(response)
        bot.reply_to(message, response)
        dhtDevice.exit()
        time.sleep(2.0)
        raise error
    
@bot.message_handler(func=lambda message: message.text == 'RunScript')
def handle_run_script_message(message):
    output = execute_bash_script()
    bot.reply_to(message, f'Bash script executed. Output:\n\n{output}')

def execute_bash_script():
    try:
        result = subprocess.run(['./test.sh'], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"Error executing Bash script: {e}")
        # Handle the error as needed
        return f"Error executing Bash script: {e}"

@bot.message_handler(func=lambda message: message.text == 'Stat')
def handle_status_message(message):
    # Read CPU temperature
    cpu_temperatures = psutil.sensors_temperatures()
    cpu_temperature = None

    if 'cpu_thermal' in cpu_temperatures:
        cpu_temperature = cpu_temperatures['cpu_thermal'][0].current
    elif 'coretemp' in cpu_temperatures:
        cpu_temperature = cpu_temperatures['coretemp'][0].current

    # Send the CPU temperature as a reply
    if cpu_temperature is not None:
        response = f'CPU Temperature: {cpu_temperature:.2f}°C'
    else:
        response = 'CPU temperature data not available.'

    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text == 'Reboot')
def handle_reboot_message(message):
    # Send a confirmation message
    bot.reply_to(message, 'Rebooting...')

    # Perform a system reboot
    subprocess.run(['sudo','/usr/sbin/reboot'])

@bot.message_handler(func=lambda message: message.text == 'Poweroff')
def handle_poweroff_message(message):
    # Ask for confirmation using inline keyboard
    confirmation_keyboard = types.InlineKeyboardMarkup()
    confirm_button = types.InlineKeyboardButton(text="Confirm", callback_data="poweroff_confirm")
    cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data="poweroff_cancel")
    confirmation_keyboard.add(confirm_button, cancel_button)

    bot.reply_to(message, "Are you sure you want to power off the Raspberry Pi?", reply_markup=confirmation_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "poweroff_confirm")
def handle_poweroff_confirmation(call):
    bot.send_message(call.message.chat.id, "Powering off...")
    os.system('sudo poweroff')

@bot.callback_query_handler(func=lambda call: call.data == "poweroff_cancel")
def handle_poweroff_cancel(call):
    bot.send_message(call.message.chat.id, "Poweroff canceled.")

# Unknown message handler
@bot.message_handler(func=lambda message: True)  # Handle all messages
def handle_unknown_message(message):
    bot.reply_to(message, "I'm sorry, I don't understand that command. Send /help to see available commands.")

def main():
    bot.polling()

if __name__ == '__main__':
    main()
