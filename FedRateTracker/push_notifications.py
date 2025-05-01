"""
Push notifications module for the financial dashboard
Uses Firebase Cloud Messaging (FCM) or web notifications API
"""

import os
import json
import requests
from datetime import datetime
import base64

class PushNotificationManager:
    """Manages push notifications for the dashboard"""
    def __init__(self):
        # Firebase Cloud Messaging credentials
        self.fcm_server_key = os.environ.get("FCM_SERVER_KEY")
        self.fcm_api_url = "https://fcm.googleapis.com/fcm/send"
        self.web_push_enabled = False
        
    def is_fcm_available(self):
        """Check if Firebase Cloud Messaging is configured"""
        return self.fcm_server_key is not None
        
    def send_fcm_notification(self, title, body, topic=None, token=None, data=None):
        """
        Send a Firebase Cloud Messaging notification
        
        Args:
            title (str): Notification title
            body (str): Notification body text
            topic (str, optional): Topic to send to (e.g., 'market_alerts')
            token (str, optional): Device token to send to specific device
            data (dict, optional): Additional data payload
            
        Returns:
            bool: Success or failure
        """
        if not self.is_fcm_available():
            print("Firebase Cloud Messaging not configured (FCM_SERVER_KEY missing)")
            return False
            
        # Set up the notification payload
        message = {
            "notification": {
                "title": title,
                "body": body,
                "click_action": "OPEN_NOTIFICATION"
            }
        }
        
        # Add data payload if provided
        if data:
            message["data"] = data
            
        # Target by topic or token
        if topic:
            message["to"] = f"/topics/{topic}"
        elif token:
            message["to"] = token
        else:
            print("Error: Either topic or token must be provided")
            return False
            
        # Send the notification
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"key={self.fcm_server_key}"
        }
        
        try:
            response = requests.post(
                self.fcm_api_url,
                headers=headers,
                data=json.dumps(message)
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == 1:
                    print(f"Successfully sent notification: {title}")
                    return True
                else:
                    print(f"Failed to send notification: {result}")
                    return False
            else:
                print(f"FCM API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending FCM notification: {e}")
            return False
            
    def generate_web_push_config(self):
        """
        Generate configuration for web push notifications
        This is used in the Streamlit app to initialize the client-side
        push notification system
        """
        config = {
            "fcm_available": self.is_fcm_available(),
            "web_push_enabled": self.web_push_enabled,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.is_fcm_available():
            config["fcm_config"] = {
                "apiKey": "YOUR_FIREBASE_API_KEY",  # Will be set by client
                "authDomain": "YOUR_FIREBASE_AUTH_DOMAIN",  # Will be set by client
                "projectId": "YOUR_FIREBASE_PROJECT_ID",  # Will be set by client
                "messagingSenderId": "YOUR_FIREBASE_MESSAGING_SENDER_ID"  # Will be set by client
            }
            
        return config
        
    def send_notification_from_alert(self, notification_data):
        """
        Send a push notification from an alert notification
        
        Args:
            notification_data (dict): The notification data from the database
            
        Returns:
            bool: Success or failure
        """
        if not self.is_fcm_available():
            return False
            
        title = notification_data.get("title", "Market Alert")
        body = f"Source: {notification_data.get('source', 'Unknown')}"
        
        if notification_data.get("stock_symbol"):
            body += f" | Symbol: {notification_data.get('stock_symbol')}"
            
        # Prepare data payload
        data = {
            "notification_id": str(notification_data.get("id", 0)),
            "timestamp": notification_data.get("timestamp").isoformat() if isinstance(notification_data.get("timestamp"), datetime) else str(notification_data.get("timestamp")),
            "url": notification_data.get("url", ""),
            "sentiment": notification_data.get("sentiment", "neutral")
        }
        
        # Send to the alerts topic
        return self.send_fcm_notification(
            title=title,
            body=body,
            topic="market_alerts",
            data=data
        )

# Generate HTML/JS for client-side push notification setup
def generate_push_notification_html():
    """Generate the HTML/JS snippet for enabling push notifications in the browser"""
    html = """
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-messaging.js"></script>
    <script>
    // Push notification setup
    document.addEventListener('DOMContentLoaded', function() {
        // Function to request notification permission
        function requestNotificationPermission() {
            if ('Notification' in window) {
                Notification.requestPermission().then(function(permission) {
                    if (permission === 'granted') {
                        console.log('Notification permission granted.');
                        initializeFirebaseMessaging();
                    } else {
                        console.log('Notification permission denied.');
                    }
                });
            }
        }
        
        // Initialize Firebase Cloud Messaging
        function initializeFirebaseMessaging() {
            // Firebase configuration would be set by the dashboard
            // This is just a placeholder for the client-side code
            const firebaseConfig = {
                apiKey: "YOUR_API_KEY",
                authDomain: "YOUR_AUTH_DOMAIN",
                projectId: "YOUR_PROJECT_ID",
                storageBucket: "YOUR_STORAGE_BUCKET",
                messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
                appId: "YOUR_APP_ID"
            };
            
            // Initialize Firebase
            if (typeof firebase !== 'undefined') {
                if (!firebase.apps.length) {
                    firebase.initializeApp(firebaseConfig);
                }
                
                const messaging = firebase.messaging();
                
                // Request permission and get token
                messaging.getToken({ vapidKey: 'YOUR_PUBLIC_VAPID_KEY' })
                    .then((currentToken) => {
                        if (currentToken) {
                            console.log('FCM token:', currentToken);
                            // Send this token to your server
                            sendTokenToServer(currentToken);
                        } else {
                            console.log('No registration token available.');
                        }
                    })
                    .catch((err) => {
                        console.log('An error occurred while retrieving token:', err);
                    });
                    
                // Handle incoming messages
                messaging.onMessage((payload) => {
                    console.log('Message received:', payload);
                    // Display notification using the Notification API
                    const notificationTitle = payload.notification.title;
                    const notificationOptions = {
                        body: payload.notification.body,
                        icon: '/icon.png',
                        data: payload.data
                    };
                    
                    new Notification(notificationTitle, notificationOptions);
                });
            }
        }
        
        // Send token to server
        function sendTokenToServer(token) {
            // This would send the token to your server
            console.log('Would send token to server:', token);
        }
        
        // Add notification button to UI
        const enableButton = document.createElement('button');
        enableButton.textContent = 'Enable Notifications';
        enableButton.className = 'notification-button';
        enableButton.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;padding:10px;background:#4CAF50;color:white;border:none;border-radius:5px;cursor:pointer;box-shadow:0 2px 5px rgba(0,0,0,0.2);';
        enableButton.onclick = requestNotificationPermission;
        
        document.body.appendChild(enableButton);
    });
    </script>
    """
    return html

# For Streamlit integration
def get_push_notification_component():
    """Get a Streamlit component for enabling push notifications"""
    manager = PushNotificationManager()
    html = generate_push_notification_html()
    
    # In Streamlit we need to use the component in a different way
    return html, manager