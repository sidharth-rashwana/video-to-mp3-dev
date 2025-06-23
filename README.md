### **Description**

This project provides a backend service for converting video files to MP3 format. It enables efficient handling and processing of media content, forming the core of a simple and scalable media conversion tool.

### **Tech Stack**

* **Backend**: FastAPI, Python
* **Database**: MongoDB
* **Containerization**: Docker

**Docker Usage**

To run the project using Docker, follow these steps:

1.Setup `.env` parameters as below :


```
MONGO_URI = '' # ATLAS MONGO URI
SENDER_EMAIL = "" # gmail sender email
APP_PASSWORD = "" # gmail app password
JWT_SECRET_KEY = ""
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 10080
JWT_RESET_TOKEN_EXPIRE_MINUTES = 10
RESET_PASSWORD_LINK="http://localhost:8000/api/auth/reset-password" # do changer this in prod env
OTP_VALIDITY_IN_MINUTES=5
OTP_VALIDITY_IN_MINUTES_SIGNUP=5
SINCH_URL=''
SINCH_TOKEN=""
SINCH_SENDER_MOBILE=""
CELERY_PATH = "/tmp/celery"
```

2.Ensure that Docker is installed on your system.

3.Open a terminal or command prompt.

4.Navigate to the project directory.

5.Run the following command:

		`sudo docker-compose build`
		`sudo docker-compose up -d`
