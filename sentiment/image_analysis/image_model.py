import tensorflow as tf
import numpy as np
import cv2

# Load the saved Keras image sentiment model
model = tf.keras.models.load_model("sentiment/image_analysis/best_model.h5")

# Define the image size used during training
IMG_SIZE = (224, 224)

def predict_image_sentiment(image_path):
    # Read the image using OpenCV
    image = cv2.imread(image_path)
    if image is None:
        return "Invalid Image", 0.0  # Return default confidence

    # Resize and scale the image
    image = cv2.resize(image, IMG_SIZE)
    image = image.astype("float32") / 255.0

    # Expand dimensions to match model input shape (1, 224, 224, 3)
    image = np.expand_dims(image, axis=0)

    # Predict
    prediction = model.predict(image, verbose=0)[0][0]  # Added verbose=0 to suppress output
    
    # Calculate confidence
    confidence = prediction if prediction >= 0.5 else 1 - prediction
    
    # Interpret result
    sentiment = "Positive" if prediction >= 0.5 else "Negative"
    
    return sentiment, float(confidence)  # Return both sentiment and confidence