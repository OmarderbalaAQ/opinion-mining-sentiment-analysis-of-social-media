# opinion-mining-sentiment-analysis-of-social-media-
Sentiment &amp; Content Analysis System This repository contains the code for my graduation project—a dual-model system that performs sentiment analysis and image content classification using both Natural Language Processing (NLP) and Computer Vision (CV) techniques.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Repository Structure](#repository-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Deployment](#deployment)
- [Results & Future Work](#results--future-work)
- [License](#license)

---



## Project Overview

This project implements a multi-modal sentiment analysis system:

- **Text Sentiment Analysis:**  
  Utilizes a Support Vector Classifier (SVC) trained on labeled text data (e.g., tweets or posts) to classify sentiment as positive or negative.

- **Image Sentiment Analysis:**  
  Uses a pretrained CNN model from **ImageNet** (e.g., ResNet, VGG) to classify images based on learned visual features. The model was fine-tuned on a custom labeled dataset of positive and negative sentiment images.

- **Web Deployment:**  
  The system is wrapped in a Django web application that accepts URLs, scrapes the page content (text and images), and returns an integrated sentiment analysis result.

---




## Features

- **Dual-Modal Analysis**: Combines natural language processing and computer vision for a more comprehensive sentiment evaluation.
- **Pretrained Image Model**: Uses powerful pretrained networks from ImageNet, fine-tuned for sentiment classification.
- **Web Scraping Integration**: Scrapes and processes real-world content from provided links.
- **Django Deployment**: Easy-to-use web interface for live testing and demonstration.

---




---


---

## Setup & Installation

### Prerequisites

- Python 3.10
- Anaconda (recommended for environment management)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/sentiment-content-analysis.git
   cd sentiment-content-analysis

### Create a Virtual Environment

conda create --name sentiment_env python=3.10
conda activate sentiment_env

### Install Requirements
pip install -r requirements.txt



## Results & Future Work
### Performance:
The text SVC model performs well on labeled sentiment datasets. The pretrained image model (fine-tuned from ImageNet) achieves promising accuracy after training on a custom dataset.

### Next Steps:

- Experiment with ensemble methods to combine text and image scores.

- Extend image labeling to multi-class sentiment.

- Optimize web scraping robustness and coverage.
