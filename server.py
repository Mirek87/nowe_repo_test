import network
import socket
import time
from machine import Pin, ADC
from secret import ssid, password
import dht  # Dodane importowanie biblioteki DHT
import onewire
import ds18x20

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)
# Define a variable to keep track of the last time data was sent
last_send_time = 0
# Inicjalizuj czujnik DHT11
dht_sensor = dht.DHT11(Pin(2))  # Ustaw odpowiedni numer pinu GPIO

# Inicjalizacja czujnika DS18B20
data_pin = Pin(16)  # Ustaw odpowiedni numer pinu GPIO
ds_sensor = ds18x20.DS18X20(onewire.OneWire(data_pin))
roms = ds_sensor.scan()

while True:
    try:
        cl, addr = s.accept()
        request = cl.recv(1024)
        print(request)

        # Odczytaj wartość wilgotności z czujnika DHT11
        dht_sensor.measure()
        humidity = dht_sensor.humidity()
        
         # Odczyt temperatury z czujnika DS18B20
        ds_sensor.convert_temp()
        time.sleep_ms(750)  # Czas na konwersję
        temperature = ds_sensor.read_temp(roms[0])

        # Sprawdź, czy minęło 5 sekund od ostatniego wysłania danych
        current_time = time.time()
        if current_time - last_send_time >= 15:
            # Konwertuj wilgotność na napis
            humidity_str = str(humidity)
            temperature_str = str(temperature)
            
            # Wyślij wilgotność i temperaturę jako odpowiedź
            response = "Wilgotność: {}% Temperatura: {}°C".format(humidity_str, temperature_str)
            cl.send(response)
            print("Wysłano dane:", response)
            
            # Zaktualizuj czas ostatniego wysłania
            last_send_time = current_time
        
        cl.close()

    except OSError as e:
        cl.close()
        print('connection closed')
