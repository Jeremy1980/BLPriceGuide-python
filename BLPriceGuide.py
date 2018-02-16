'''
Created on 08 February 2018
Updated on 11 February 2018

@author: Jarema Czajkowski <jeremy.cz@wp.pl>
@license: Eclipse Public License version 2.0
@version: 2018c
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
from datetime import datetime
from copy import deepcopy


'''
global constants
'''
__appdescription__ = 'A utility to help you know price of selected LEGO element with chosen currency and color, using BrickLink catalog price guide.'
__appname__ = 'BLPriceGuide';

__version__ = '2018c'
__compilation__ = 'Python 2.7.13 :: Anaconda 4.4.0 on win32'

__configfilename__ = os.path.join(os.path.expanduser("~") ,__appname__.lower() +'.cfg')
__partsdbfilename__ = os.path.join(os.path.expanduser("~") ,__appname__.lower() + 'parts.csv')

__basecurrency__ = 'PLN'

__partsdb_maxfields__ = 4

__year__ = datetime.today().strftime('%Y')
__today__ = datetime.today().strftime('%Y-%m-%d')

__rebrickable_apikey__ = 'bq2yXWJUt2'   
__rebrickable_allcolors__ = 'https://rebrickable.com/api/v3/lego/parts/%s/colors/?key=%s'   #Get a list of all Colors a Part has appeared in.
__rebrickable_color__ = 'https://www.rebrickable.com/api/v3/lego/colors/%d/?key=%s'         #Get details about a specific Color.
__rebrickable_parts__ = 'https://www.rebrickable.com/api/v3/lego/parts/?key=%s&bricklink_id=%s'

__bricklink_colors__ = [
#SolidColors
'1','2','3','4','5','6','7','8','9','10','11','103','104','105','106','109','110'
,'120','150','152','153','154','155','156','157','158','160','161','165','166'
,'23','24','25','26','27','28','29','31','32','33','34','35','36','37','38','39'
,'40','41','42','43','44','47','48','49','54','55','56','58','59','62','63','68'
,'69','71','72','73','76','80','85','86','87','88','89','90','91','93','94','96','97','99'
#TransparentColors
,'12','13','17','18','98','164','121','19','16','108','20','14','74','15','113','114','51','50','107'
#ChromeColors
,'21','22','57','122','52','64','82'
#PearlColors
,'83','119','66','95','77','78','61','115','81','84'
#MetalicColors
,'67','70','65'
#MilkyColors
,'60','159','46','118'
#GlitterColors
,'101','163','162','102','100'
#SpeckleColors
,'111','151','116','117'
#ModulexColors
,'123','124','125','126','127','128','131','134','132','133','129','130','135','136','137','138','139'
,'141','140','142','146','143','144','145','147','148','149'
                        ]


'''
global variables
'''
_priceguidelink = 'https://www.bricklink.com/catalogPG.asp?P=%s&colorID=%d&viewExclude=N&v=P&cID=Y'
_rateslink = 'https://api.fixer.io/latest?base=%s'
_partsdblink = 'http://www.jaremaczajkowski.pl/pub/bricklink/parts.txt'

_resultfilename = os.path.join(os.path.dirname(__file__) ,__appname__.lower())

_inlinecookie = 'BLNEWSESSIONID=B0E73E566049BFEE196AE756071D904D; viewCurrencyID=114; isCountryID=PL; ASPSESSIONIDSSASDTDB=OILJICKCDBKBAFKKMBOHEAKB; blckMID=1617b83375d00000-304116216285974f; blckSessionStarted=1; cartBuyerID=-356842332'
_currencyList = {}
_config = None
_partdb = None

'''
methods
'''
def writeconfig():
    if _config:
        with open(__configfilename__ ,'w') as configfile:
            _config.write(configfile)    

def split_host(line):
    return splithost(splittype(line)[1])[0]
        
def print_currencies(maxcolumn):
    ncolumn = 0
    line = ''
    for key in sorted(_currencyList.keys()):
        ncolumn = ncolumn +1
        line = '%s%s\t' %(line,key)
        if ncolumn == maxcolumn:
            print line
            line = ''
            ncolumn = 0

def print_colors(element):
    if _config.has_section(element):
        for k,v in _config[element].items():
            print '%s\t%s' % (k,v)
            
def collect_colors(element):
    def net_errmsg(errno):
        if errno==404:
            print 'Not Found Element %s.' % element
        else:
            print 'Unable connect to %s [%d].' % (rbhost,errno)  
    
    def parse_errmsg():
        print 'Unable to parse result from %s' % rbhost
        
    errno = 200
    rbhost = split_host(__rebrickable_parts__)             
    opener = build_opener()
    opener.addheaders = [
     ('Host' ,rbhost)
    ,('User-agent' ,'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0')
    ,('Accept' ,'text/plain,application/json;q=0.9,*/*;q=0.8')
    ]
    
    try:
        print 'Fetching data... (this may take a while)' 
        response = opener.open(__rebrickable_parts__ % (__rebrickable_apikey__,element))
    except URLError as error:    
        net_errmsg(error.code)               
    else:
        try:
            rbdata = json.load(response)
        except:
            parse_errmsg()
        else:
            try:
                part_num = rbdata['results'][0]['part_num']
            except:
                net_errmsg(404)    
            else:
                try:
                    response = opener.open(__rebrickable_allcolors__ % (part_num,__rebrickable_apikey__))
                except URLError as error:
                    net_errmsg(404)
                else:
                    if response:            
                        try:
                            rbdata = json.load(response)['results']
                        except Exception as error:
                            rbdata = {}      
                        else:
                            blcolors = {}                    
                            for v in rbdata:
                                try:
                                    response = opener.open(__rebrickable_color__ % (v['color_id'],__rebrickable_apikey__))         
                                except URLError as error:
                                    pass
                                else:
                                    try:
                                        external_ids = json.load(response)
                                    except:
                                        pass    
                                    else:
                                        try:
                                            blcolors[str(external_ids['external_ids']['BrickLink']['ext_ids'][0])] = external_ids['name']
                                        except:
                                            pass  
                                          
                            if blcolors:
                                blcolors = sorted(blcolors.items())      
                                _config[element] = {}
                                _config[element].update(blcolors)   
                                writeconfig() 


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
    return (float(cval) ,float(cval) * float(rate))

def get_partimgtag(content):
    clen = 0
    maxlen = content.__len__()
    cc = deepcopy(content)
    cc = cc.replace('<IMG','<img')
    while clen < maxlen:    
        rstart = cc.lower().find('<img',clen)
        if rstart == -1:
            clen = clen +1
        else:
            rend = cc.lower().find('>',rstart)
            imgtag = cc[rstart:rend +1]
            clen = clen + imgtag.__len__()
            if imgtag.find(args.element+'.')<>-1:
                return imgtag.lower()
    return ''    

def get_shopanchor(line):
    astart = line.lower().find('<a')
    aend = line.lower().find('</a')
    a = ''
    name = ''
    href = ''
    result = ''
    if astart <> -1:
        a = line[astart:aend +4]
        la= a.lower()
        argstart = la.find('alt=')
        arglen = 4 +1
        if argstart == -1:
           argstart = la.find('title=')
           arglen = 6 +1 
        if argstart <> -1:
            argstart = argstart +arglen
            argend = la.find('"',argstart)
            name = a[argstart:argend]
            hrefstart = la.find('href=')
            if hrefstart == -1:
                result = name
            else:
                hrefend = la.find('"',hrefstart +5 +1)
                href = 'http://%s%s' % (split_host(_priceguidelink),a[hrefstart +5 +1:hrefend])
                result = '<a href="%s" target="bricklink">%s</a>' % (href,name)
   
    return (a,result,name,href)

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
    parser.add_argument('-c' ,'--color' ,default=11 ,type=int ,metavar='INTEGER'
        ,help='Chosen Color for pieces. Default is eleven /black/')
    parser.add_argument('-o'  ,'--output-currency' ,default=__basecurrency__ ,metavar='CURRENCY'
        ,help='The chosen output Currency from supported kinds. Default it %s' % __basecurrency__)
    
    parser.add_argument('--list-currencies' ,metavar='COLUMN' ,nargs=1  
                        ,help='Display supported Currencies and exit. You can define the number of columns displayed, or leave default value ')
    parser.add_argument('--list-colors' ,action='store_true'
                        ,help='print a list of all Colors a Element has appeared in and exit')        

    arggroup = parser.add_argument_group("required arguments")
    arggroup.add_argument('-e'  ,'--element' ,required=True
        ,help='The chosen identificator of LEGO Element')

    if sys.argv.__len__() == 1:
        parser.print_help()
        sys.exit(0)
    
    if sys.argv.count('--list-currencies') == 0:    
        args = parser.parse_args()
        args.output_currency = args.output_currency.upper()


#ConfigParser
    _config = configparser.ConfigParser()
    _config.optionxform = str 
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

    if _config.has_option('links' ,'partsdb'):
        _partsdblink = _config['links']['partsdb']
    else:
        _config['links']['partsdb'] = _partsdblink

    if _config.has_option('data' ,'cookie'):
        _inlinecookie = _config['data']['cookie']
    else:
        _config['data']['cookie'] = _inlinecookie

    if not os.path.exists(__configfilename__):
        _config['data']['historicalrates'] = '0000-00-00'
        writeconfig()


#StockExchange
    response= None
    success = True
    if _config.has_section(__today__):
        _currencyList.update(_config[__today__])
    else:
        try:
            response = urlopen(_rateslink % __basecurrency__)
        except URLError as error:
            success = False
        else:
            if response:
                try:
                    _currencyList = json.load(response)['rates']
                except Exception as error:
                    print error
                    success = False

                    
#CurrencyList    
    if success and (not _config.has_section(__today__)):
        for key in _config.keys():
            if key.startswith(__year__):
                _config[key] = {}
                del _config[key]
        _config[__today__] = _currencyList
        _config['data']['historicalrates'] = __today__
        writeconfig()
        
    if not success:
        rdata = _config['data']['historicalrates']
        if _config.has_section(rdata):
            _currencyList.update(_config[__today__])
        else:
            print 'Unable connect to: '+split_host(_rateslink)
            sys.exit(1)
    _currencyList[__basecurrency__] = 1.0
            
    if sys.argv.count('--list-currencies') <> 0:
        if sys.argv.__len__() == 3: 
            val = sys.argv[2] 
            if val in ['1','2','3','4','5','6','7','8','9']:
                val = int(val)
            else:
                val = 3
        else: 
            val = 3
        print_currencies(val)
        sys.exit(0)      
        
    if not _currencyList.has_key(args.output_currency):
        print_currencies(3)
        print 'The selected currency %s is unsupported. Choose one from the list above.' % args.output_currency
        sys.exit(1)
                 
                   
#BrickLink:Colors
    if not _config.has_section(args.element):
        collect_colors(args.element)
        
    if args.list_colors:
        print_colors(args.element)
        sys.exit(0)   
                    
    if not _config.has_option(args.element, args.color):
        if _config.has_section(args.element):
            print 'The selected Color number %s is not assigned officially to Element %s. \nChoose one from the list displayed with --list-colors argument.' % (args.color,args.element);
        if not str(args.color) in __bricklink_colors__:
            print '\nColor number %s is not valid.' % args.color
            sys.exit(1);
        else:
            print '\nColor number %s is recognized as official BrickLink Color.' % args.color        
                   
                    
#BrickLink::Parts
    if not os.path.exists(__partsdbfilename__):
        try:
            response = urlopen(_partsdblink)
        except:
            pass
        else:
            try:
                with open(__partsdbfilename__ ,'w') as partsdb:
                    partsdb.write(response.read())
            except:
                if os.path.exists(__partsdbfilename__):
                    os.unlink(__partsdbfilename__)
        
    if os.path.exists(__partsdbfilename__):
        with open(__partsdbfilename__ ,'r') as partsdb:
            for line in partsdb.readlines():
                data = line.split('\t')
                if data.__len__() == __partsdb_maxfields__:
                    if data[2] == args.element:
                        _partdb = data                        
                    
                    
#BrickLink::PriceGuide
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
        print error
    else:
        if response is not None:
            content = re.sub(r"\s+" ," " ,response.read()).lower()
            result = []
            print
            for line in content.split('<table'):
                cidx = 0
                crows = ''
                while cidx < line.__len__():
                    tr = get_tr(line[cidx:])
                    if tr:
                        shopanchor = get_shopanchor(tr)
                        if shopanchor[1]:
                            basecurrency = __basecurrency__.lower()
                            crate = exchange(tr[tr.find(basecurrency)+basecurrency.__len__():])

                            tr = tr.replace(basecurrency ,args.output_currency)
                            tr = tr.replace(str(crate[0]) ,str(crate[1]))
                            tr = tr.replace(shopanchor[0] ,shopanchor[1]) 
                            crows = crows +tr +os.linesep
                            print '%s\t%s\t\t%s' % (args.output_currency ,str(crate[1]) ,shopanchor[2])
                        cidx = cidx +tr.__len__()
                    else:
                        cidx = cidx +1

                if crows:
                    result.append(crows)
            print
            if result:
                _resultfilename = _resultfilename +'-%s.html' % args.element
                
                partimagetag = get_partimgtag(content)
                if partimagetag:
                    headertr = '<tr><th colspan="'+str(result.__len__()+1)+'">'+partimagetag+'</th></tr>'
                else:
                    headertr = ''
                    
                headerth= '<th colspan="'+str(result.__len__()+1)+'"><font size="4" color="#FFFFFF">Current Items for Sale:</font></th>'
                headertr= headertr+os.linesep+'<tr bgcolor="#5E5A80" align="CENTER">'+headerth+'</tr>'
                
                forsave = '<html><table cellspacing="0" cellpadding="5" border="0" align="CENTER">'
                if _partdb:
                    forsave = forsave+'<caption><h2>%s [%s, %s]</h2></caption>' % (_partdb[3],_partdb[2],_partdb[1])
                forsave = forsave+headertr+'<tr valign="TOP">'                
                
                for rows in result:
                    forsave = forsave+'<td><table cellspacing="0" cellpadding="5" border="0">'+rows+'</table></td>' 
                forsave = forsave+'</tr></table></html>'
                try:
                    with open(_resultfilename ,'w') as resultfile:
                        resultfile.write(forsave)
                except Exception as error:
                    print error
                else:
                    print 'Result saved to %s' % _resultfilename
            else:
                print 'Nothing to save.'
        else:
            print 'Nothing to save.'

