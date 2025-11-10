import tensorflow as tf
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.applications import MobileNetV2


IMG_SIZE = 128
ColorChannels = 3
MODEL_WEIGHTS_PATH = 'ModelWeights.weights.h5'

def load_model_structure():
    """
    Defines and returns the MobileNetV2 model structure.
    """
    input_tensor = Input(shape=(IMG_SIZE, IMG_SIZE, ColorChannels))
    baseModel = MobileNetV2(pooling='avg',
                            include_top=False,
                            input_tensor=input_tensor)
    headModel = baseModel.output
    headModel = Dense(1, activation="sigmoid")(headModel)
    model = Model(inputs=baseModel.input, outputs=headModel)
    return model

print("[INFO] Loading Keras model...")
model = load_model_structure()
model.load_weights(MODEL_WEIGHTS_PATH)
print("[INFO] Model loaded successfully.")


print("[INFO] Converting model to TFLite...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)


converter.optimizations = [tf.lite.Optimize.DEFAULT]

tflite_model = converter.convert()


with open("model.tflite", "wb") as f:
    f.write(tflite_model)

print(f"[SUCCESS] Model converted and saved as 'model.tflite'")