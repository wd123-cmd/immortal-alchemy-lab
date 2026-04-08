import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image
import difflib
import re

# -------------------------------
# 1. THE BULLETPROOF RAYCASTER ENGINE
# -------------------------------
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

def get_herb_aliases(herb_name):
    """Maps actual herb names to known OCR hallucinations."""
    aliases = []
    
    mapping = {
        "healing sunflower": ["healing", "sunflower", "sundlng", "hcalig", "healig", "sunllower", "sunllowe", "hcaling", "suadlag"],
        "black iron root": ["black", "ironroot", "ionadoot", "bladz", "bonroor", "bouroot", "bladk", "kourooc", "bledk"],
        "blue wave coral herb": ["blue", "wave", "coral", "ballaz", "coaileb", "ualheb", "oalhub", "blugwav", "blugwavg", "uallub"],
        "thousand year lotus": ["thousand", "lotus", "hatsud", "yealoug", "yeaclos", "ibousand", "tbousand", "uouard", "iboutnd", "ycclas"],
        "moonlight jade leaf": ["moonlight", "jadeleaf", "saglui", "mopnlight", "meccligbt", "jadalzar", "jadeleal", "jadelea", "mooclight", "meonligbt", "jadglca"],
        "ironbone grass": ["ironbone", "gtass", "iobge", "kuboue", "ouboue", "bonbone", "konbong"],
        "nine suns flame grass": ["ninesuns", "flamegrass"],
        "purple lightning orchid": ["purple", "orchid", "lightning", "bistadattg"],
        "red ginseng": ["ginseng", "red"],
        "bitter jade grass": ["bitter", "jadegrass"],
        "cloud mist herb": ["cloud", "mist", "mistherb", "candmse", "hedb"],
        "spirit spring herb": ["spiritspring", "springherb"],
        "dandelion of qi": ["dandelion", "ofqi"],
        "seven star flower": ["sevenstar", "starflower", "setcnsaac", "flower"],
        "starlight dew herb": ["starlight", "dewherb"],
        "heavenly spirit vine": ["heavenly", "spiritvine"],
        "mountain green herb": ["mountain", "greenherb"],
        "wild spirit grass": ["wildspirit", "wild", "budspide", "gas3"],
        "azure serpent grass": ["azure", "serpent"],
        "wild bitter grass": ["wildbitter", "bittergrass"]
    }
    
    if herb_name.lower() in mapping:
        aliases.extend(mapping[herb_name.lower()])
        
    return list(set(aliases))

def decompile_screenshot(image_file, herb_list):
    reader = load_ocr()
    image = Image.open(image_file)
