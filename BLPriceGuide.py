'''
Created on 08 February 2018

@author: Jarema Czajkowski <jeremy.cz@wp.pl>
@license: Eclipse Public License version 2.0
@version: 2018a
@note: A utility to help you know price of selected LEGO element with chosen currency,
using BrickLink catalog price guide.
'''

import re
import sys
import os
import argparse
import json
import configparser

from urllib2 import *


'''
global constants
'''
__appdescription__ = 'A utility to help you know price of selected LEGO element with chosen currency and color, using BrickLink catalog price guide.'
__appname__ = 'BLPriceGuide';

__configfilename__ = os.path.join(os.path.expanduser("~") ,__appname__.lower() +'.cfg')
__resultfilename__ = os.path.join(os.path.dirname(__file__) ,__appname__.lower() +'.html')

__version__ = '2018a'
__compilation__ = 'Python 2.7.13 :: Anaconda 4.4.0 on win32'

__basecurrency__ = 'PLN'


'''
global variables
'''
_priceguidelink = 'https://www.bricklink.com/catalogPG.asp?P=%s&colorID=%d&viewExclude=N&v=P&cID=Y'
_rateslink = 'https://api.fixer.io/latest?base=%s'

_inlinecookie = 'BLNEWSESSIONID=B0E73E566049BFEE196AE756071D904D; viewCurrencyID=114; isCountryID=PL; ASPSESSIONIDSSASDTDB=OILJICKCDBKBAFKKMBOHEAKB; blckMID=1617b83375d00000-304116216285974f; blckSessionStarted=1; cartBuyerID=-356842332'
_currencyList = {}
_config = None


'''
methods
'''
def print_currencies():
    for key in _currencyList.keys():
        print key

def get_rate(ckey):
    try:
        return _currencyList[ckey]
    except:
        return -1

def exchange(line):
    cval = ''
    for x in range(line.__len__()):
        if line[x] == '<':
            break
        if line[x] in ['.',',','0','1','2','3','4','5','6','7','8','9']:
            cval = cval + line[x]
    rate = get_rate(args.output_currency)
    return (float(cval) ,float(cval) * rate)

def split_host(line):
    return splithost(splittype(line)[1])[0]

def format_shopname(line):
    rstart = line.find('<a')
    rend = line.find('</a')
    if rstart == -1:
        result = ''

    a = line[rstart:rend +4]
    rstart = a.find('alt=')
    if rstart == -1:
        result = ''
    else:
        rend = a.find('"' ,rstart +5)
        result = a[rstart +5:rend]
    return(a ,result)

def get_tr(line):
    rstart = line.find('<tr')
    rend = line.find('</tr')
    if rstart == -1:
        return ''

    result = line[rstart:rend +5]
    cidx = result.find(__basecurrency__.lower())
    if cidx == -1:
        return ''
    else:
        rstart = cidx+__basecurrency__.__len__()
        if result[rstart:rstart +6] == '&nbsp;' or result[rstart:rstart +1] == ' ':
            return result
        else:
            return ''


'''
main procedure
'''
if __name__ == '__main__':
#ArgumentParser
    parser = argparse.ArgumentParser(description=__appdescription__)

    parser.add_argument('-v' ,'--version' ,action='version'
        ,version='%s %s (%s compilation)' % (__appname__ ,__version__ ,__compilation__))
    parser.add_argument('-c' ,'--color' ,default=0 ,type=int ,metavar='INTEGER'
        ,help='Chosen color for pieces. Default is zero /black/')

    arggroup = parser.add_argument_group("required")
    arggroup.add_argument('-e'  ,'--element' ,required=True
        ,help='The chosen identificator of LEGO element')
    arggroup.add_argument('-o'  ,'--output-currency' ,required=True ,metavar='CURRENCY'
        ,help='The chosen output currency from supported kinds')

    if sys.argv.__len__() == 1:
        parser.print_help()
        sys.exit(-1)

    args = parser.parse_args()
    args.output_currency = args.output_currency.upper()


#ConfigParser
    _config = configparser.ConfigParser()
    _config.read(__configfilename__)

    if not _config.has_section('links'):
        _config['links'] = {}
    if not _config.has_section('data'):
        _config['data'] = {}

    if _config.has_option('links' ,'priceguide'):
        _priceguidelink = _config['links']['priceguide'].replace('%%' ,'%')
    else:
        _config['links']['priceguide'] = _priceguidelink.replace('%' ,'%%')

    if _config.has_option('links' ,'exchangerates'):
        _rateslink = _config['links']['exchangerates'].replace('%%' ,'%')
    else:
        _config['links']['exchangerates'] = _rateslink.replace('%' ,'%%')

    if _config.has_option('data' ,'cookie'):
        _inlinecookie = _config['data']['cookie']
    else:
        _config['data']['cookie'] = _inlinecookie

    _config.update()
    if not os.path.exists(__configfilename__):
        with open(__configfilename__ ,'w') as configfile:
            _config.write(configfile)


#StockExchange
    response = None
    try:
        response = urlopen(_rateslink % __basecurrency__)
    except URLError as error:
        print 'Unable connect to '+split_host(_rateslink)
        sys.exit(error.errno)
    else:
        if response is not None:
            try:
                _currencyList = json.load(response)['rates']
            except Exception as error:
                print error.message
                sys.exit(-1)

            _currencyList[__basecurrency__] = 1.0
            if not _currencyList.has_key(args.output_currency):
                print_currencies()
                print 'The selected currency %s is unsupported. Choose one from the list above.' % args.output_currency
                sys.exit(-1)


#BrickLink
    response = None
    try:
        print 'Working... (this may take a while)'
        opener = build_opener()
        opener.addheaders = [
        ('Host' ,split_host(_priceguidelink))
        ,('User-agent' ,'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0')
        ,('Accept' ,'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        ,('Cookie' ,_inlinecookie)
        ]
        response = opener.open(_priceguidelink % (args.element ,args.color))
    except Exception as error:
        print error.message
    else:
        if response is not None:
            content = re.sub(r"\s+" ," " ,response.read()).lower()
            result = ''
            for line in content.split('<table'):
                cidx = 0
                table = ''
                while cidx < line.__len__():
                    tr = get_tr(line[cidx:])
                    if tr:
                        sname = format_shopname(tr)
                        if sname[1]:
                            crate = exchange(tr[tr.find(__basecurrency__.lower())++__basecurrency__.__len__():])

                            tr = tr.replace(__basecurrency__.lower() ,args.output_currency)
                            tr = tr.replace(str(crate[0]) ,str(crate[1]))
                            tr = tr.replace(sname[0] ,sname[1])
                            table = table +tr
                        cidx = cidx +tr.__len__()
                    else:
                        cidx = cidx +1

                if table:
                    result = result + '<table>' + table + '</table>'

            if result:
                try:
                    with open(__resultfilename__ ,'w') as resultfile:
                        resultfile.write(result)
                except Exception as error:
                    print error.message
                else:
                    print 'Result saved to %s' % __resultfilename__
            else:
                print 'Nothing to save.'

