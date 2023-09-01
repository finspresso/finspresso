#include <SD.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x3F,16,2);  // set the LCD address to 0x27 for a 16 chars and 2 line display

File myFile;

#define analogPin  A0 //the thermistor attach to
#define beta 3950 //the beta of the thermistor
#define chipSelectPin 53

float TReference = 298.0; // Reference temperature in Kelvin of the resistor
float KelvinOffset = 273.0; // 0°C expressed in Kelvin
int analogReadResolution = 1024;


void setup()
{
  Serial.begin(9600);
  Serial.print("Initializing SD card...");
  // On the Ethernet Shield, CS is pin 4. It's set as an output by default.
  // Note that even if it's not used as the CS pin, the hardware SS pin
  // (10 on most Arduino boards, 53 on the Mega) must be left as an output
  // or the SD library functions will not work.
   pinMode(chipSelectPin, OUTPUT);

  if (!SD.begin(chipSelectPin)) {
    Serial.println("SD card initialization failed!");
    return;
  }
  Serial.println("SD card initialization done.");

  Serial.print("Trying to init I2C LED\n");
  lcd.init();
  Serial.print("I2C LED init complete\n");
  lcd.backlight();

}

void loop()
{
  long VinAnalog = analogRead(analogPin);
  float tempK = beta / (log(analogReadResolution / float(VinAnalog) - 1) + beta / TReference); //TK=beta/(ln(RT/RN)+beta/TN)
  float tempC = kelvinToCentigradeClecius(tempK);
  lcd.clear();
  lcd.print(tempC);
  lcd.print("C");
  writeToSD(tempC);
  Serial.print("Temp: ");
  Serial.print(tempC);
  Serial.println("°C");
  delay(1000);

}

float kelvinToCentigradeClecius(float tempK)
{
  return tempK - KelvinOffset;
}

void writeToSD(float tempC) {
  myFile = SD.open("temp.txt", FILE_WRITE);
  // if the file opened okay, write to it:
  if (myFile) {
    long execTime = millis() / 1e3;
    myFile.print(execTime);
    myFile.print("s, ");
    myFile.print(tempC);
    myFile.println("C");
    myFile.close();
  } else {
    // if the file didn't open, print an error:
    Serial.println("error opening file");
  }
}
