# CashCam
![icon_small](https://github.com/user-attachments/assets/abd3257d-f239-47de-a877-5704a8095d5a)

CashCam is an innovative app that allows users to take pictures of cash in different currencies (USD, EURO, ILS), detects and classifies the coins and bills, sums up the total amount, calculates the equivalent in a desired currency, and returns the annotated image with the information back to the user.

## Who Can Use the App

### Tourists
CashCam is perfect for tourists who are unfamiliar with specific currencies while traveling. By simply snapping a picture of their cash, they can quickly understand the total amount and convert it to their desired currency.

### Businesses
Businesses can use CashCam to keep track of daily revenues. By saving pictures of their daily income, the app documents the amounts in the form of informative images that not only display the total amount but also visually show the counted coins and bills.

## Deep Learning Model

- **Location**: The deep learning model is hosted on a server.
- **Functionality**: Detects and classifies the cash objects (coins and bills) within each image.
- **Training**: Trained on tens of thousands of images to ensure high accuracy.
- **Architecture**: Built using YOLOv8, a state-of-the-art object detection model.

## App Features

- **Backend**: Built using Python and FastAPI for efficient performance.
- **Frontend**: Developed using Flutter for a smooth user experience.
- **Platform**: Currently available for iPhone and Android support.
- **Exchange Rates**: Real-time and daily updated exchange rates are fetched to provide accurate currency conversions.
- **Google Registration**: Users can easily register through their Google account.
- **Server Communication**: The app communicates with a server for sending images to the detection model and receiving classification results, as well as interacting with a database for user data.

## Server & Database

- **Database**: SQLite Db. Stores user information and image history. Local cache is also used for logs and fetched data.
- **Detection Model**: The server runs the detection and classification model.
- **Communication**: The app seamlessly communicates with the server for image processing and data storage.

## Expandability

The app is currently set up to handle USD, EURO, and ILS, but can easily be expanded to support more currencies. By adding new datasets and updating the model, the app can detect and classify additional currencies from around the world, making it a versatile tool for more users.

## Authors

This project was developed by:

- [UriB1](https://github.com/UriBeeri)
- [ItayE97](https://github.com/ItayE97)
- [RoDanielle](https://github.com/RoDanielle)
- [YuvalHajbi](https://github.com/YuvalHajbi)
- [Ronmegini](https://github.com/ronmegini)
