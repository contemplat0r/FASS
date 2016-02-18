
# -*- coding: utf8 -*- 

import httplib
from lxml import etree
from StringIO import StringIO
import codecs
from copy import deepcopy
import requests
import csv
import itertools
import functools


#def site_processor(base_url, layer_processors_stack):
#    #current_layer_processor = layer_processors_stack.pop()
#    while layer_processors_stack.not_empty():
#        current_layer_processor = layer_processors_stack.pop()
#        processed_current_layer_info = 

def single_site_url_processor(url, processor):
    processing_result = processor.process(url)
    return processing_result

def process_all_pages_with_base_url(base_url, layer_num, layers_processor_storage):
    all_pages_processing_result = []
    processor = layers_processor_storage.get(layer_num)
    processing_result = processor(base_url)
    info = processing_result.get_info()
    next_page_url = processing_result.get_next_page()
    next_layer_urls = processing_result.get_next_layer_urls()
    next_layer_num = layer_num + 1
    next_layer_results = []
    if next_layer_urls != None and layers_processor_storage.is_layer_processor_with_num(next_layer_num):
        for next_layer_url in next_layer_urls:
            next_layer_results.append(process_all_pages_with_base_url(next_layer_url, next_layer_num, layers_processor_storage))
    all_pages_processing_result.append(processor.combine(info, next_layer_results))
    while next_page_url != None:
        processing_result = processor(next_page_url)
        info = processing_result.get_info()
        next_page_url = processing_result.get_next_page()
        next_layer_urls = processing_result.get_next_layer_urls()
        next_layer_num = layer_num + 1
        next_layer_results = []
        if next_layer_urls != None and layers_processor_storage.is_layer_processor_with_num(next_layer_num):
            for next_layer_url in next_layer_urls:
                next_layer_results.append(process_all_pages_with_base_url(next_layer_url, next_layer_num, layers_processor_storage))
        all_pages_processing_result.append(processor.combine(info, next_layer_results))
    
    return processor.all_pages_results_combine(all_pages_processing_result)
