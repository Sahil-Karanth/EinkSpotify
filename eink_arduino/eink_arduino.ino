#include <Arduino.h>
#include "EPD.h"
#include "pic_scenario.h"
#include <WiFiMulti.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>

WiFiMulti wifiMulti;
Preferences preferences;

const char* mdns_hostname = "sahil-epaper";
const char* config_ap_ssid = "EPaper-Config";
const char* config_ap_password = "configure123"; // not a secret XD

#define Max_CharNum_PerLine 37
#define CONFIG_KEY 2  // button for entering config mode

extern uint8_t ImageBW[ALLSCREEN_BYTES];

WebServer server(80);

struct WiFiNetwork {
    String ssid;
    String password;
    bool isHome;
};

std::vector<WiFiNetwork> savedNetworks;
String homeNetworkSSID = "";

//======================================================================
// Configuration Functions
//======================================================================

void loadNetworksFromStorage() {
    preferences.begin("wifi-config", false);
    
    // Load home network SSID
    homeNetworkSSID = preferences.getString("home_ssid", "");
    
    // Load network count
    int networkCount = preferences.getInt("network_count", 0);
    
    savedNetworks.clear();
    for (int i = 0; i < networkCount; i++) {
        WiFiNetwork network;
        network.ssid = preferences.getString(("ssid_" + String(i)).c_str(), "");
        network.password = preferences.getString(("pwd_" + String(i)).c_str(), "");
        network.isHome = (network.ssid == homeNetworkSSID);
        
        if (network.ssid.length() > 0) {
            savedNetworks.push_back(network);
        }
    }
    preferences.end();
}

void saveNetworksToStorage() {
    preferences.begin("wifi-config", false);
    
    // Save home network SSID
    preferences.putString("home_ssid", homeNetworkSSID);
    
    // Save network count
    preferences.putInt("network_count", savedNetworks.size());
    
    // Save each network
    for (int i = 0; i < savedNetworks.size(); i++) {
        preferences.putString(("ssid_" + String(i)).c_str(), savedNetworks[i].ssid);
        preferences.putString(("pwd_" + String(i)).c_str(), savedNetworks[i].password);
    }
    
    preferences.end();
}

void addNetworkToMulti() {
    wifiMulti = WiFiMulti(); // Reset WiFiMulti
    
    // Add home network first (higher priority)
    for (const auto& network : savedNetworks) {
        if (network.isHome) {
            wifiMulti.addAP(network.ssid.c_str(), network.password.c_str());
            Serial.println("Added network: " + network.ssid + " (HOME - PRIORITY)");
        }
    }
    
    // Then add other networks
    for (const auto& network : savedNetworks) {
        if (!network.isHome) {
            wifiMulti.addAP(network.ssid.c_str(), network.password.c_str());
            Serial.println("Added network: " + network.ssid + " (Firebase mode)");
        }
    }
}

//======================================================================
// Configuration Web Pages
//======================================================================

void handleConfigRoot() {
    String html = "<!DOCTYPE html><html><head><title>EPaper WiFi Config</title>";
    html += "<style>";
    html += "body { font-family: Arial; margin: 20px; }";
    html += ".network { border: 1px solid #ccc; padding: 10px; margin: 10px 0; }";
    html += ".home { background-color: #e8f5e8; }";
    html += "button { margin: 5px; padding: 8px 15px; }";
    html += "input { margin: 5px; padding: 5px; }";
    html += "</style></head><body>";
    html += "<h1>EPaper WiFi Configuration</h1>";
    html += "<h2>Current Networks</h2><div id='networks'>";

    for (int i = 0; i < savedNetworks.size(); i++) {
        html += "<div class='network" + String(savedNetworks[i].isHome ? " home" : "") + "'>";
        html += "<strong>" + savedNetworks[i].ssid + "</strong>";
        if (savedNetworks[i].isHome) {
            html += " <em>(HOME - mDNS mode)</em>";
        } else {
            html += " <em>(Firebase mode)</em>";
        }
        html += "<br>";
        html += "<button onclick='setHome(\"" + savedNetworks[i].ssid + "\")'>Set as Home</button>";
        html += "<button onclick='deleteNetwork(\"" + savedNetworks[i].ssid + "\")'>Delete</button>";
        html += "</div>";
    }

    html += "</div><h2>Add New Network</h2>";
    html += "<form action='/add_network' method='POST'>";
    html += "<input type='text' name='ssid' placeholder='Network Name (SSID)' required><br>";
    html += "<input type='password' name='password' placeholder='Password' required><br>";
    html += "<label><input type='checkbox' name='is_home'> Set as Home Network</label><br>";
    html += "<button type='submit'>Add Network</button></form>";
    html += "<h2>Actions</h2>";
    html += "<button onclick='location.href=\"/restart\"'>Restart Device</button>";
    html += "<button onclick='location.href=\"/exit_config\"'>Exit Config Mode</button>";
    
    html += "<script>";
    html += "function setHome(ssid) {";
    html += "fetch('/set_home', {";
    html += "method: 'POST',";
    html += "headers: {'Content-Type': 'application/x-www-form-urlencoded'},";
    html += "body: 'ssid=' + encodeURIComponent(ssid)";
    html += "}).then(() => location.reload());";
    html += "}";
    html += "function deleteNetwork(ssid) {";
    html += "if (confirm('Delete network \"' + ssid + '\"?')) {";
    html += "fetch('/delete_network', {";
    html += "method: 'POST',";
    html += "headers: {'Content-Type': 'application/x-www-form-urlencoded'},";
    html += "body: 'ssid=' + encodeURIComponent(ssid)";
    html += "}).then(() => location.reload());";
    html += "}";
    html += "}";
    html += "</script></body></html>";

    server.send(200, "text/html", html);
}

void handleAddNetwork() {
    if (server.hasArg("ssid") && server.hasArg("password")) {
        String ssid = server.arg("ssid");
        String password = server.arg("password");
        bool isHome = server.hasArg("is_home");
        
        // Check if network already exists
        bool exists = false;
        for (auto& network : savedNetworks) {
            if (network.ssid == ssid) {
                network.password = password;
                network.isHome = isHome;
                exists = true;
                break;
            }
        }
        
        if (!exists) {
            WiFiNetwork newNetwork;
            newNetwork.ssid = ssid;
            newNetwork.password = password;
            newNetwork.isHome = isHome;
            savedNetworks.push_back(newNetwork);
        }
        
        if (isHome) {
            // Clear other home designations
            for (auto& network : savedNetworks) {
                if (network.ssid != ssid) {
                    network.isHome = false;
                }
            }
            homeNetworkSSID = ssid;
        }
        
        saveNetworksToStorage();
        server.sendHeader("Location", "/", true);
        server.send(302, "text/plain", "");
    } else {
        server.send(400, "text/plain", "Missing SSID or password");
    }
}

void handleSetHome() {
    if (server.hasArg("ssid")) {
        String ssid = server.arg("ssid");
        
        // Clear all home designations
        for (auto& network : savedNetworks) {
            network.isHome = (network.ssid == ssid);
        }
        
        homeNetworkSSID = ssid;
        saveNetworksToStorage();
        server.send(200, "text/plain", "Home network set");
    } else {
        server.send(400, "text/plain", "Missing SSID");
    }
}

void handleDeleteNetwork() {
    if (server.hasArg("ssid")) {
        String ssid = server.arg("ssid");
        
        for (int i = 0; i < savedNetworks.size(); i++) {
            if (savedNetworks[i].ssid == ssid) {
                savedNetworks.erase(savedNetworks.begin() + i);
                break;
            }
        }
        
        if (homeNetworkSSID == ssid) {
            homeNetworkSSID = "";
        }
        
        saveNetworksToStorage();
        server.send(200, "text/plain", "Network deleted");
    } else {
        server.send(400, "text/plain", "Missing SSID");
    }
}

void handleRestart() {
    server.send(200, "text/plain", "Restarting...");
    delay(1000);
    ESP.restart();
}

void handleExitConfig() {
    server.send(200, "text/plain", "Exiting config mode...");
    delay(1000);
    ESP.restart();
}

//======================================================================
// Normal Operation Functions
//======================================================================

void handleUpdate() {
    if (server.hasArg("message")) {
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

        // cache the response
        preferences.begin("display-cache", false);
        preferences.putString("display_cache", received_message);
        preferences.end();
        
        server.send(200, "text/plain", "OK. Message displayed.");
    } else {
        server.send(400, "text/plain", "ERROR. 'message' parameter not found.");
    }
}

void readAndDisplayFromFirebase() {
    HTTPClient http;
    String url = "https://eink-spotify-middleman-default-rtdb.firebaseio.com/messages/from_device/sahil.json";

    http.begin(url);
    int httpCode = http.GET();

    if (httpCode == 200) {
        String payload = http.getString();
        Serial.println("Firebase payload:");
        Serial.println(payload);

        const size_t capacity = JSON_OBJECT_SIZE(2) + 100;
        DynamicJsonDocument doc(capacity);
        DeserializationError error = deserializeJson(doc, payload);

        if (error) {
            Serial.print("deserializeJson() failed: ");
            Serial.println(error.f_str());
        } else {
            String message = doc["message"] | "";
            Serial.println("Displaying message: " + message);
            
            EPD_Init();
            EPD_Clear(0, 0, 296, 128, WHITE);
            EPD_ALL_Fill(WHITE);
            EPD_Update();
            EPD_Clear_R26H();
            
            Long_Text_Display(0, 0, message.c_str(), 24, BLACK);
            EPD_DisplayImage(ImageBW);
            EPD_FastUpdate();
        }
    } else {
        Serial.printf("Firebase GET failed: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();

    // Sleep for 12 hours
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    esp_sleep_enable_timer_wakeup(43200LL * 1000000ULL);
    esp_deep_sleep_start();
}

//======================================================================
// Main Functions
//======================================================================

void enterConfigMode() {
    Serial.println("Entering configuration mode...");
    
    // Display config mode message
    EPD_Init();
    EPD_Clear(0, 0, 296, 128, WHITE);
    EPD_ALL_Fill(WHITE);
    EPD_Update();
    EPD_Clear_R26H();
    
    Long_Text_Display(0, 0, "Config Mode\nConnect to:\nEPaper-Config\nPassword: configure123\nVisit http://192.168.4.1", 16, BLACK);
    EPD_DisplayImage(ImageBW);
    EPD_FastUpdate();
    EPD_Sleep();
    
    // Start AP mode
    WiFi.mode(WIFI_AP);
    WiFi.softAP(config_ap_ssid, config_ap_password);
    
    Serial.println("Config AP started");
    Serial.print("IP address: ");
    Serial.println(WiFi.softAPIP());
    
    // Setup config web server
    server.on("/", handleConfigRoot);
    server.on("/add_network", HTTP_POST, handleAddNetwork);
    server.on("/set_home", HTTP_POST, handleSetHome);
    server.on("/delete_network", HTTP_POST, handleDeleteNetwork);
    server.on("/restart", handleRestart);
    server.on("/exit_config", handleExitConfig);
    server.begin();
    
    Serial.println("Config server started at http://192.168.4.1");
    
    // Stay in config mode
    while (true) {
        server.handleClient();
        delay(10);
    }
}

void setup() {
    Serial.begin(9600);
    delay(100);

    // Setup pins
    pinMode(7, OUTPUT);
    digitalWrite(7, HIGH);
    // pinMode(HOME_KEY, INPUT_PULLUP);
    pinMode(CONFIG_KEY, INPUT_PULLUP);

    // Check if config button is pressed during startup
    if (digitalRead(CONFIG_KEY) == LOW) {
        delay(100);
        if (digitalRead(CONFIG_KEY) == LOW) {
            enterConfigMode();
        }
    }

    // Load saved networks
    loadNetworksFromStorage();
    
    // If no networks saved, enter config mode
    if (savedNetworks.empty()) {
        Serial.println("No networks configured. Entering config mode...");
        enterConfigMode();
    }
    
    // Add networks to WiFiMulti
    addNetworkToMulti();
    
    // Initialize display
    EPD_Init();
    EPD_Clear(0, 0, 296, 128, WHITE);
    EPD_ALL_Fill(WHITE);
    EPD_Update();
    EPD_Clear_R26H();
    
    Long_Text_Display(0, 0, "Connecting to WiFi...", 24, BLACK);
    EPD_DisplayImage(ImageBW);
    EPD_FastUpdate();
    EPD_Sleep();
    
    // Try to connect
    if (wifiMulti.run() == WL_CONNECTED) {
        String connectedSSID = WiFi.SSID();
        Serial.println("Connected to: " + connectedSSID);
        
        // Check if this is the home network
        bool isHomeNetwork = (connectedSSID == homeNetworkSSID);
        
        if (isHomeNetwork) {
            Serial.println("Home network detected - starting mDNS mode");
            
            if (!MDNS.begin(mdns_hostname)) {
                Serial.println("Error setting up mDNS responder!");
                while(1) { delay(1000); }
            }
            
            server.on("/update", handleUpdate);
            server.begin();
            Serial.println("HTTP server started at http://epaper.local");
            
            // Display ready message
            EPD_Init();
            EPD_Clear(0, 0, 296, 128, WHITE);
            EPD_ALL_Fill(WHITE);
            EPD_Update();
            EPD_Clear_R26H();
            
            preferences.begin("display-cache", false);
            String old_display_value = preferences.getString("display_cache", "Ready!\nhttp://epaper.local");
            preferences.end();

            Long_Text_Display(0, 0, old_display_value.c_str(), 24, BLACK);

            EPD_DisplayImage(ImageBW);
            EPD_FastUpdate();
            EPD_Sleep();
            
        } else {
            Serial.println("Non-home network detected - starting Firebase mode");
            readAndDisplayFromFirebase();
        }
        
    } else {
        Serial.println("WiFi connection failed");
        
        // Display error and enter config mode
        EPD_Init();
        EPD_Clear(0, 0, 296, 128, WHITE);
        EPD_ALL_Fill(WHITE);
        EPD_Update();
        EPD_Clear_R26H();
        
        Long_Text_Display(0, 0, "WiFi Failed\nEntering config mode...", 24, BLACK);
        EPD_DisplayImage(ImageBW);
        EPD_FastUpdate();
        EPD_Sleep();
        
        delay(2000);
        enterConfigMode();
    }
}

void loop() {
    server.handleClient();
    
    // Check for config button press
    if (digitalRead(CONFIG_KEY) == LOW) {
        delay(100);
        if (digitalRead(CONFIG_KEY) == LOW) {
            Serial.println("Config button pressed");
            enterConfigMode();
        }
    }
    
}

// Rest of your existing functions...
void Long_Text_Display(int x, int y, const char* content, int fontSize, int color) {
    char line[Max_CharNum_PerLine + 1];
    int lineLength = 0;
    
    for (int i = 0; content[i] != '\0'; i++) {
        char c = content[i];

        if (c == '\n') {
            line[lineLength] = '\0';
            EPD_ShowString(x, y, line, color, fontSize);
            y += fontSize;
            lineLength = 0;
            continue;
        }

        if (lineLength < Max_CharNum_PerLine) {
            line[lineLength++] = c;
        }

        if (lineLength >= Max_CharNum_PerLine) {
            line[lineLength] = '\0';
            EPD_ShowString(x, y, line, color, fontSize);
            y += fontSize;
            lineLength = 0;
        }
    }

    if (lineLength > 0) {
        line[lineLength] = '\0';
        EPD_ShowString(x, y, line, color, fontSize);
    }
}