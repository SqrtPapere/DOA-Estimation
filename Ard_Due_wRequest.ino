#include <SPI.h>

#define CONVST 8 
#define RD 10
#define BUSY 9
#define numSamples 40000
#define CLK 10

const byte mics[8]= {B10001000, B11001000, B10011000, B11011000, B10101000, B11101000, B10111000, B11111000}; //array of commands for adc
byte x=0; byte y=0;  //Storage for ADC result high and low byte
unsigned short data[numSamples];  //Storage for data (word/uns short stores a 16-bit unsigned number)

unsigned long timeStart;
unsigned long timeEnd;

float voltage = 0;

void sampleMic(byte mic, int i){
  x=SPI.transfer(mic); 
  y=SPI.transfer(B00000000);// Filler //SPI transfer is based on a simultaneous send and receive: the received data is returned in y. 
  delayMicroseconds(2);  //This delay is necessary to meet Tacq time (see datasheet p5). Change to 3us if voltage reads low
    
  //Trigger a conversion with a fast pulse
  noInterrupts();
  REG_PIOC_SODR |= (0x01 << 22);
  REG_PIOC_CODR |= (0x01 << 22);
  interrupts(); 
  //Wait for conversion to be finished
  delayMicroseconds(4);
  //store ADC result in data
  data[i]= ((unsigned short) x<<8) | (unsigned short) y;
}

void setup() {
  SerialUSB.begin(115200);
  SPI.begin();
  SPI.setClockDivider(CLK); //a number from 1 to 255//Set for 8Mhz SPI (The default setting is SPI_CLOCK_DIV4, which sets the SPI clock to one-quarter the frequency of the system clock (4 Mhz for the boards at 16 MHz like mine)).
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0); //clock polarity and phase(the base value of the clock is zero, i.e. the idle state is 0 and active state is 1.)
  pinMode(CONVST, OUTPUT);
  pinMode(RD, OUTPUT);
  pinMode(BUSY, INPUT);
  digitalWrite(CONVST, LOW);  //Set CONVST low by default
  digitalWrite(RD, LOW);  //Set and keep RD (SS) low
}

void loop() {
  if(SerialUSB.available()){
    SerialUSB.read();
    for (int i=0;i<numSamples+1;i++){
    sampleMic(mics[i&B00000111], i);
    }

   for (int i=1;i<numSamples+1;i++){    
    if((i-1)%8 == 0 && i != 1){
      SerialUSB.print(F("\n"));
     }
     SerialUSB.print(data[i]);
     SerialUSB.print(",");
     delayMicroseconds(100);
     }
  }
  //timeStart = micros();
  //timeEnd = micros();
  //Serial.println(timeEnd -timeStart); // 408920 us
}  
