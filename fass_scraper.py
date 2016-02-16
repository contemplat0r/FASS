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

from htmlutils import get_all_same_type_nodes, generate_attrib_getter, node_list_processor


def layer_processor(pages_generator, single_page_processor, compound_function):
    first_page_processing_result =  single_page_processor(pages_generator.next())
    return reduce(lambda result, page: compound_function(result, single_page_processor(page)), pages_generator, first_page_processing_result)


class HTTProcessor(object):

    def __init__(self, headers=None):
        self._session = requests.Session()
        self._headers = headers
        self._status = None
        self._response = None
        self._last_exception = None
        self._response = None
        self._timeout = None

    def set_headers(self, headers):
        self._headers = headers

    def set_timeout(self, timeout):
        self._timeout = timeout

    def prepare_request(self, command, data):
        pass

    def send_request(self, url, content_type=None, headers=None, post_data=None):
        response = None
        self._headers = self._session.headers
        if headers == None and self._headers != None:
           headers = self._headers 
        self._response = None
        try: 
            if post_data == None:
                response = self._session.get(url, headers=headers)
            elif post_data == {}:
                response = self._session.post(url, headers=headers)
            else:
                response = self._session.post(url, headers=headers, data=post_data)
            self._last_exception = None
            self._response = response
            self._status = response.status_code
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError, httplib.IncompleteRead, requests.exceptions.MissingSchema) as exception:
                                                        
            print 'send_request: ' + url + '  Exception: ' + str(exception) + '\n'
            self._last_exception = exception
        return self.get_content_as(content_type)


    def send_prepared_request(self):
        pass

    def get_status(self):
        return self._status

    def get_last_exception(self):
        return self._last_exception

    def get_response(self):
        return self._response

    def get_content_as(self, content_type='text'):
        if self._response != None:
            if content_type == 'text':
                return self._response.text
            elif content_type == 'binary':
                return self._response.content
            elif content_type == 'json':
                return self._response.json
            elif content_type == 'raw':
                return self._response.raw
            else:
                return self._response.text
        else:
            return None



def get_content(url, headers={'User-Agent' : 'requests'}, post_data=None, exceptions_log_file=None):
    req = None
    content = None
    try: 
        if post_data == None:
            req = requests.get(url, headers=headers)
            print dir(req)
        elif post_data == {}:
            req = requests.post(url, headers=headers)
        else:
            req = requests.post(url, headers=headers, data=post_data)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError, httplib.IncompleteRead, requests.exceptions.MissingSchema) as e:
        print 'get_content: ' + url + '  Exception: ' + str(e) + '\n'
        if exceptions_log_file != None:
            exceptions_log_file.write('get_content: ' + url + ' Exception: ' + str(e) + '\n')
            exceptions_log_file.flush()
    if req != None:
        content = req.text

    return content


if __name__ == '__main__':


    headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0 Iceweasel/42.0',
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language' : 'ru-RU,ru;q=0.7,uk;q=0.3',
            'Connection' : 'keep-alive',
            'Cache-Control' : 'max-age=0'
            }
    site_url = 'http://www.fass.se'
    base_url = 'http://www.fass.se/LIF'
    first_layer_url = 'http://www.fass.se/LIF/pharmaceuticalliststart?userType=2'
    second_layer_url_static_part = 'http://www.fass.se/LIF/pharmaceuticallist?userType=2&page='
    third_layer_url_static_part = 'http://www.fass.se/LIF/product?userType=2&'
    parser = etree.HTMLParser()
    
    result_data = list()

    
    #first_layer_content = get_content(first_layer_url, headers)
    #first_layer_tree = etree.parse(StringIO(first_layer_content), parser)

    #first_layer_info_container_xpath = '//div[@class="abcpanel"]/div/ul/li/a/span'
    first_layer_info_container_xpath = '//div[@class="abcpanel"]/div/ul/li/a'
    second_layer_info_container_xpath = '//li[@class="tradeNameList"]'
    second_layer_trade_name_xpath = 'a/span[@class="innerlabel"]'
    second_layer_product_link_xpath = 'ul/li[@class="linkList"]/a'
    second_layer_product_description_text_xpath = 'ul/li[@class="linkList"]/a/div/span[@class="innerlabel"]'
    third_layer_info_container_xpath = '//div[@class="list-box substance"]/ul/li/a/span'
    
    '''
    first_layer_info_container = first_layer_tree.xpath(first_layer_info_container_xpath)
    for item in first_layer_info_container[:2]:
        print item.text.encode('utf-8')
        second_layer_url = second_layer_url_static_part + item.text
        print second_layer_url
        second_layer_content = get_content(second_layer_url, headers)
        second_layer_tree = etree.parse(StringIO(second_layer_content), parser)
        second_layer_info_container = second_layer_tree.xpath(second_layer_info_container_xpath)
        product_description_dict = {'Produkt' : '', 'Beredningsform Styrka' : '', 'NPLid' : '', 'Aktiv substans' : '', 'Url' : ''}
        for product_description in second_layer_info_container[:3]:
            #print product_description
            product_name = product_description.xpath(second_layer_trade_name_xpath)
            print product_name[0].text.encode('utf-8')
            product_description_dict['Produkt'] = product_name[0].text.encode('utf-8')
            product_description_text_container = product_description.xpath(second_layer_product_description_text_xpath)
            product_description_text_subcontainer = product_description_text_container[0]
            #print 'product_description_text_subcontainer: ', product_description_text_subcontainer
            child_list = product_description_text_subcontainer.getchildren()
            product_description_text = ''
            if child_list == []:
                product_description_text = product_description_text_subcontainer.text
            else:
                product_description_text = child_list[0].tail

            if product_description_text != '' and product_description_text.find(', ') != -1:
                product_description_text = product_description_text[product_description_text.find(', ') + 2:]

            print 'product_description_text: ', product_description_text
            product_description_dict['Beredningsform Styrka'] = product_description_text.encode('utf-8')
            product_links = product_description.xpath(second_layer_product_link_xpath)
            for link in product_links:
                product_description_dict_copy = deepcopy(product_description_dict)
                link_string = link.attrib.get('href')
                link_string_parts = link_string.split('&')
                #print link_string_parts
                third_layer_url = third_layer_url_static_part + link_string_parts[1]
                print third_layer_url
                third_layer_content = get_content(third_layer_url, headers)
                third_layer_tree = etree.parse(StringIO(third_layer_content), parser)
                third_layer_info_container = third_layer_tree.xpath(third_layer_info_container_xpath)
                #print third_layer_info_container
                print third_layer_info_container[0].text
                nplid = link_string_parts[1]
                nplid = nplid[nplid.find('=') + 1:]
                product_description_dict_copy['NPLid'] = nplid
                product_description_dict_copy['Aktiv substans'] = third_layer_info_container[0].text.encode('utf-8')
                product_description_dict_copy['Url'] = third_layer_url
                result_data.append(product_description_dict_copy)

    fieldnames = ['Produkt', 'Beredningsform Styrka', 'NPLid', 'Aktiv substans', 'Url']
    result_file = open('medical_list.csv', 'wb')
    csv_writer = csv.DictWriter(result_file, fieldnames=fieldnames, delimiter='|')
    headers = dict((name, name) for name in fieldnames)
    csv_writer.writerow(headers)
    csv_writer.writerows(result_data)
    result_file.flush()
    result_file.close()
    '''

    http_processor = HTTProcessor(headers=headers)

    content = http_processor.send_request(site_url, 'text')

    get_href_attrib = generate_attrib_getter('href')
    second_layer_url_maker = lambda link_node: base_url + get_href_attrib(link_node)[1:]
    content = http_processor.send_request(first_layer_url, 'text')
    second_layer_link_nodes = get_all_same_type_nodes(content, first_layer_info_container_xpath)
    second_layer_urls = node_list_processor(second_layer_link_nodes, second_layer_url_maker)
    for second_layer_url in second_layer_urls[:3]:
        print second_layer_url
        content = http_processor.send_request(second_layer_url, 'text')
        #print content

    
