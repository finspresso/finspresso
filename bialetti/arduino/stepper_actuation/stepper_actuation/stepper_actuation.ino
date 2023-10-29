#include <Stepper.h>

const int stepsPerRevolution = 2048; // change this to fit the number of steps per revolution
const int rolePerMinute = 10;        // Adjustable range of 28BYJ-48 stepper is 0~17 rpm
int currentState = -1;

//set steps and the connection with MCU
Stepper stepper(stepsPerRevolution, 2, 3, 4, 5);
bool clockwise = false;
void setup()
{
  Serial.begin(9600);
  stepper.setSpeed(rolePerMinute);
    pinMode(7, INPUT);
}

bool switchOn()
{
  int switchState = digitalRead(2);
  if (switchState != currentState) {
    currentState = switchState;
    if (currentState == 1) {
      Serial.println("Switch in on state");
    } else {
      Serial.println("Switch in off state");
    }
  }
  if (currentState == 1) {
      return true;
    } else {
      return false;
    }
}

void loop()
{
  // Serial.println("Stepping");
  // int val = 2 * 2048;
  // stepper.step(val);  //Turn the motor in val steps
  // delay(1000);
  int i = 0;
  int target_steps = stepsPerRevolution / 2;
  while (i < target_steps) {
    if (switchOn()) {
      if (clockwise) {
        stepper.step(-1);
      } else {
        stepper.step(1);
      }
      i++;
    }
  }

  Serial.println("Reached target_steps");
  exit(0);

}
