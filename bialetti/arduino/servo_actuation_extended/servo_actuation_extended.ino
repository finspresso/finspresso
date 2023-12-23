
#include <Servo.h>

Servo myservo;//create servo object to control a servo
bool finished;
int initAngle = 180;
int pwmPin = 9;
void setup()
{
  Serial.begin(9600);
  Serial.println("Init");
  myservo.attach(pwmPin);//attachs the servo on pin 9 to servo object
  myservo.write(initAngle);
  finished = false;
}


void goToPosition(int targetPosition) {
  // Move to zero position smoothly
  int currentPosition = myservo.read();
  if (currentPosition > targetPosition) {
    while (currentPosition > targetPosition) {
        myservo.write(currentPosition - 1);
        delay(15);
        currentPosition = myservo.read();
    }
  } else {
        while (currentPosition < targetPosition) {
          myservo.write(currentPosition + 1);
          delay(15);
          currentPosition = myservo.read();
    }
  }
}

void loop()
{
  int deltaAngleDegree = 90;
  int currentPosition = myservo.read();
  int targetPosition = 0;
  if (currentPosition > deltaAngleDegree) {
    targetPosition = currentPosition - deltaAngleDegree;
  } else {
    targetPosition = currentPosition + deltaAngleDegree;
  }
  goToPosition(targetPosition);
  goToPosition(initAngle);

}
