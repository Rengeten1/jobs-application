import sys
import os
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models import Config

db = SessionLocal()
def update_config(k, v):
    item = db.query(Config).filter(Config.key == k).first()
    if not item:
        db.add(Config(key=k, value=v))
    else:
        item.value = v

keywords = "Machine Learning Internship, Deep Learning Intern, Artificial Intelligence Intern, Computer Vision Intern, AI Engineering Intern, Data Science Internship, TinyML, Embedded AI Intern, Python Developer Intern, Munich, Germany, Remote"
profile = "I am Rownak Deb Kabya, a B.Sc. Artificial Intelligence student at the Deggendorf Institute of Technology in Germany (DAAD Scholar). I am applying for this role to fulfill a full-time mandatory semester internship requirement for my degree, ideally starting in August 2026 for a duration of several months. My technical expertise includes Python, C++, TensorFlow, Scikit-learn, and embedded AI (TinyML/ESP32). I have hands-on experience building end-to-end ML classification pipelines, developing sensor data pipelines, and NLP chatbots. I speak fluent English (C1), Portuguese (B2), and have basic German (A2)."

update_config("TARGET_KEYWORDS", keywords)
update_config("PROFILE_INFO", profile)
db.commit()
db.close()
print("Successfully inserted config into database.")
