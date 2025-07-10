#include <Arduino.h>
#include "EPD.h"            // E-paper display library
#include "pic_scenario.h"   // Header file containing image data
#include <WiFi.h>           // Wi-Fi library
#include <WebServer.h>      // Web server library
#include <ESPmDNS.h>        // mDNS library


const char* ssid = "";
const char* password = "";
const char* mdns_hostname = "epaper";

#define Max_CharNum_PerLine 37
extern uint8_t ImageBW[ALLSCREEN_BYTES];

WebServer server(80);

void displayNewText(const char* text);
void Long_Text_Display(int x, int y, const char* content, int fontSize, int color);

char *My_content_1 = "It boasts a high resolution of 272*792, offering a vivid display effect, and features the classic black and white display, suitable for various application scenarios. Support multiple development environments (Arduino IDE, ESP IDF, MicroPython), suitable for different people's needs, simplifying the secondary development process. Due to its excellent characteristics such as low power consumption, high contrast, and high reflectivity, this electronic paper screen is widely applicable to shelf tags, price tags, badges, smart tags, smart home devices, e-readers, smart wearable devices, and other portable devices, making it an ideal choice for various smart devices and applications.";
char *My_content_2 = "we got a request";

//======================================================================
// web server routes
//======================================================================
void handleUpdate() {
  String message = "No message found";
  if (server.hasArg("message")) {
    message = server.arg("message");
    Serial.print("SUCCESS: Message received -> ");
    Serial.println(message);

    EPD_Init();                     // Initialize the EPD e-paper display
    EPD_Clear(0, 0, 296, 128, WHITE); // Clear the area from (0,0) to (296,128) on the screen, background color is white
    EPD_ALL_Fill(WHITE);           // Fill the entire screen with white
    EPD_Update();                  // Update the screen display content to make the clear operation take effect
    EPD_Clear_R26H();              // Clear the R26H area of the screen

    Long_Text_Display(0, 0, My_content_2, 16, BLACK); // THIS DISPLAY DOESN'T WORK!

    EPD_DisplayImage(ImageBW);    // Display the image stored in the ImageBW array
    EPD_FastUpdate();             // Quickly update the screen content
    //  EPD_PartUpdate(); // Commented-out code, possibly used to update a part of the screen
    EPD_Sleep();                  // Set the screen to sleep mode to reduce power consumption
    
    server.send(200, "text/plain", "OK. Message displayed.");
  } else {
    server.send(400, "text/plain", "ERROR. 'message' parameter not found.");
  }
}

void setup() {

  // serial for debugging
  Serial.begin(115200);
  delay(100);

  // turn on screen
  pinMode(7, OUTPUT);
  digitalWrite(7, HIGH);

  // wifi connect
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // mDNS setup
  if (!MDNS.begin(mdns_hostname)) {
    Serial.println("Error setting up mDNS responder!");
    while(1) { delay(1000); }
  }
  Serial.printf("mDNS responder started. Hostname: http://%s.local\n", mdns_hostname);

  // web server configure
  server.on("/update", handleUpdate);
  server.begin();
  Serial.println("HTTP server started.");
  
  EPD_Init();                     // Initialize the EPD e-paper display
  EPD_Clear(0, 0, 296, 128, WHITE); // Clear the area from (0,0) to (296,128) on the screen, background color is white
  EPD_ALL_Fill(WHITE);           // Fill the entire screen with white
  EPD_Update();                  // Update the screen display content to make the clear operation take effect
  EPD_Clear_R26H();              // Clear the R26H area of the screen

  Long_Text_Display(0, 0, My_content_1, 16, BLACK); // THIS DISPLAY WORKS

  EPD_DisplayImage(ImageBW);    // Display the image stored in the ImageBW array
  EPD_FastUpdate();             // Quickly update the screen content
  //  EPD_PartUpdate(); // Commented-out code, possibly used to update a part of the screen
  EPD_Sleep();                  // Set the screen to sleep mode to reduce power consumption
}

void loop() {
  // Check for incoming web server requests
  server.handleClient();
}

// function provided by offical demo code
void Long_Text_Display(int x, int y, const char* content, int fontSize, int color) {
  int length = strlen(content);
  int i = 0;
  char line[Max_CharNum_PerLine + 1];
  while (i < length) {
    int lineLength = 0;
    memset(line, 0, sizeof(line));
    while (lineLength < Max_CharNum_PerLine && i < length) {
      line[lineLength++] = content[i++];
    }
    
    // Check if the character is a newline and skip it for display
    if (line[0] == '\n' || line[0] == '\r') {
        // Find the start of the actual content
        int contentStart = 0;
        while(contentStart < lineLength && (line[contentStart] == '\n' || line[contentStart] == '\r')) {
            contentStart++;
        }
        // Move the content to the start of the line buffer
        memmove(line, line + contentStart, lineLength - contentStart);
        line[lineLength - contentStart] = '\0';
    }
    EPD_ShowString(x, y, line, color, fontSize);
    y += fontSize;
    if (y >= 128) {
      break;
    }
  }
}

// function provided by offical demo code
void clear_all() {
  EPD_Init();
  EPD_Clear(0, 0, 296, 128, WHITE);
  EPD_ALL_Fill(WHITE);
  EPD_Update();
  EPD_Clear_R26H();
}
