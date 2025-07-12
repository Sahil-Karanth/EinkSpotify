#include <Arduino.h>
#include "EPD.h"            // E-paper display library
#include "pic_scenario.h"   // Header file containing image data
// #include <WiFi.h>           // Wi-Fi library
#include <WiFiMulti.h>
#include <WebServer.h>      // Web server library
#include <ESPmDNS.h>        // mDNS library
#include "secrets.h"

WiFiMulti wifiMulti;


const char* mdns_hostname = "epaper";

#define Max_CharNum_PerLine 37
extern uint8_t ImageBW[ALLSCREEN_BYTES];

WebServer server(80);

void displayNewText(const char* text);
void Long_Text_Display(int x, int y, const char* content, int fontSize, int color);

char *startup_message = "No data :(";

//======================================================================
// web server routes
//======================================================================
void handleUpdate() {
  if (server.hasArg("message")) {
    // 1. Declare received_message as a String object
    String received_message = server.arg("message");
    
    Serial.print("SUCCESS: Message received -> ");
    Serial.println(received_message);

    EPD_Init();
    EPD_Clear(0, 0, 296, 128, WHITE);
    EPD_ALL_Fill(WHITE);
    EPD_Update();
    EPD_Clear_R26H();

    Long_Text_Display(0, 0, received_message.c_str(), 24, BLACK);

    EPD_DisplayImage(ImageBW);
    EPD_FastUpdate();
    EPD_Sleep();
    
    server.send(200, "text/plain", "OK. Message displayed.");
  } else {
    server.send(400, "text/plain", "ERROR. 'message' parameter not found.");
  }
}

//======================================================================
// main functions
//======================================================================

void setup() {

  // serial for debugging
  Serial.begin(9600);
  delay(100);

  // turn on screen
  pinMode(7, OUTPUT);
  digitalWrite(7, HIGH);

  wifiMulti.addAP(HOME_WIFI_SSID, HOME_WIFI_PWD);
  wifiMulti.addAP("FlatWiFi", "flatpass");

  if (wifiMulti.run() == WL_CONNECTED) {
    String ssid = WiFi.SSID();
    Serial.println("Connected to: " + ssid);

    if (ssid == "EE-Hub-54Cn") {
      // mDNS mode
      if (!MDNS.begin(mdns_hostname)) {
        Serial.println("Error setting up mDNS responder!");
        while(1) { delay(1000); }
      }

      // web server configure
      server.on("/update", handleUpdate);
      server.begin();
      Serial.println("HTTP server started.");


    } else {
      // Firebase mode
    }
  } else {
    // fallback to WiFiManager or config portal
  }

  
  EPD_Init();                     // Initialize the EPD e-paper display
  EPD_Clear(0, 0, 296, 128, WHITE); // Clear the area from (0,0) to (296,128) on the screen, background color is white
  EPD_ALL_Fill(WHITE);           // Fill the entire screen with white
  EPD_Update();                  // Update the screen display content to make the clear operation take effect
  EPD_Clear_R26H();              // Clear the R26H area of the screen

  Long_Text_Display(0, 0, startup_message, 24, BLACK); // THIS DISPLAY WORKS

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
    char line[Max_CharNum_PerLine + 1];
    int lineLength = 0;
    
    // Loop through each character of the content string
    for (int i = 0; content[i] != '\0'; i++) {
        char c = content[i];

        // If we hit a newline character, draw the current line and move down
        if (c == '\n') {
            line[lineLength] = '\0'; // End the current line
            EPD_ShowString(x, y, line, color, fontSize);
            y += fontSize;           // Move down
            lineLength = 0;          // Reset for the next line
            continue;                // Skip to the next character
        }

        // Add the character to our line buffer
        if (lineLength < Max_CharNum_PerLine) {
            line[lineLength++] = c;
        }

        // If the line is now full, draw it and reset
        if (lineLength >= Max_CharNum_PerLine) {
            line[lineLength] = '\0';
            EPD_ShowString(x, y, line, color, fontSize);
            y += fontSize;
            lineLength = 0;
        }
    }

    // After the loop, draw any remaining text in the buffer
    if (lineLength > 0) {
        line[lineLength] = '\0';
        EPD_ShowString(x, y, line, color, fontSize);
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
