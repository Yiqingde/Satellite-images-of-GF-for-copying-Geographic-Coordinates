import sys


from threading import currentThread
import numpy as np



# from Py6S import *
from osgeo import gdal,gdal_array



def parse_rpc_file(rpc_file):
    # rpc_file:.rpc�ļ��ľ���·��
    # rpc_dict������RPC���µ�16���ؼ��ֵ��ֵ�
    # �ο���ַ��http://geotiff.maptools.org/rpc_prop.html��
    # https://www.osgeo.cn/gdal/development/rfc/rfc22_rpc.html
 
    rpc_dict = {}
    with open(rpc_file) as f:
        text = f.read()
 
    # .rpc�ļ��е�RPC�ؼ���
    words = ['errBias', 'errRand', 'lineOffset', 'sampOffset', 'latOffset',
             'longOffset', 'heightOffset', 'lineScale', 'sampScale', 'latScale',
             'longScale', 'heightScale', 'lineNumCoef', 'lineDenCoef','sampNumCoef', 'sampDenCoef',]
 
    # GDAL���Ӧ��RPC�ؼ���
    keys = ['ERR_BIAS', 'ERR_RAND', 'LINE_OFF', 'SAMP_OFF', 'LAT_OFF', 'LONG_OFF',
            'HEIGHT_OFF', 'LINE_SCALE', 'SAMP_SCALE', 'LAT_SCALE',
            'LONG_SCALE', 'HEIGHT_SCALE', 'LINE_NUM_COEFF', 'LINE_DEN_COEFF',
            'SAMP_NUM_COEFF', 'SAMP_DEN_COEFF']
 
    for old, new in zip(words, keys):
        text = text.replace(old, new)
    # �ԡ�;\n����Ϊ�ָ���
    text_list = text.split(';\n')
    # ɾ�����õ���
    text_list = text_list[3:-2]
    #
    text_list[0] = text_list[0].split('\n')[1]
    # ȥ���Ʊ�������з����ո�
    text_list = [item.strip('\t').replace('\n', '').replace(' ', '') for item in text_list]
 
    for item in text_list:
        # ȥ����=��
        key, value = item.split('=')
        # ȥ����������š�(������)��
        if '(' in value:
            value = value.replace('(', '').replace(')', '')
        rpc_dict[key] = value
 
    for key in keys[:12]:
        # Ϊ������ӷ��š�+��
        if not rpc_dict[key].startswith('-'):
            rpc_dict[key] = '+' + rpc_dict[key]
        # Ϊ��һ���������־��ӵ�λ
        if key in ['LAT_OFF', 'LONG_OFF', 'LAT_SCALE', 'LONG_SCALE']:
            rpc_dict[key] = rpc_dict[key] + ' degrees'
        if key in ['LINE_OFF', 'SAMP_OFF', 'LINE_SCALE', 'SAMP_SCALE']:
            rpc_dict[key] = rpc_dict[key] + ' pixels'
        if key in ['ERR_BIAS', 'ERR_RAND', 'HEIGHT_OFF', 'HEIGHT_SCALE']:
            rpc_dict[key] = rpc_dict[key] + ' meters'
 
    # ������������
    for key in keys[-4:]:
        values = []
        for item in rpc_dict[key].split(','):
            #print(item)
            if not item.startswith('-'):
                values.append('+'+item)
            else:
                values.append(item)
            rpc_dict[key] = ' '.join(values)

    return rpc_dict
def write_rpc_to_tiff(inputpath,ap = True,outpath = None):
    rpc_file = inputpath.replace('tiff', 'rpb')
    rpc_dict = parse_rpc_file(rpc_file)
    print(rpc_dict.keys())
    if ap:
        # ���޸Ķ�ȡ
        dataset = gdal.Open(inputpath,gdal.GA_Update)
        # ��tifӰ��д��rpc����Ϣ
        # ע�⣬������Ȼд����RPC����Ϣ����ʵ��Ӱ��û�н���ʵ�ʵ�RPCУ��
        # ������ЩRS/GIS�ܼ���RPC����Ϣ�������ж�̬У��
        for k in rpc_dict.keys():
            dataset.SetMetadataItem(k, rpc_dict[k], 'RPC')
        dataset.FlushCache()
        del dataset
    else:
        dataset = gdal.Open(inputpath,gdal.GA_Update)
        tiff_driver= gdal.GetDriverByName('Gtiff')
        out_ds = tiff_driver.CreateCopy(outpath, dataset, 1) 
        for k in rpc_dict.keys():
            out_ds.SetMetadataItem(k, rpc_dict[k], 'RPC')
            out_ds.FlushCache()
        del out_ds,dataset
def rpc_correction(inputpath,corrtiff,dem_tif_file = None):
    #����·�� ���·�� de m
    ## ����rpcУ���Ĳ���
    # ԭͼ������Ӱ��ȱʧֵ����Ϊ0�����Ӱ������ϵΪWGS84(EPSG:4326), �ز�������Ϊ˫���Բ�ֵ��bilinear���������ڽ���near�������ξ����cubic���ȿ�ѡ)
    # ע��DEM�ĸ��Ƿ�ΧҪ��ԭӰ��ķ�Χ�󣬴��⣬DEM������ȱʧֵ����ȱʧֵ�ᱨ��
    # ͨ��DEM��ˮ����û��ֵ�ģ���ȱʧֵ��������������Ҫ�����������Ϊ0��������RPCУ��ʱ�ᱨ��
    # ����ʹ�õ�DEM�����0ֵ���SRTM V4.1 3�뻡�ȵ�DEM(�ֱ���Ϊ90m)
    # RPC_DEMINTERPOLATION=bilinear  ��ʾ��DEM�ز���ʹ��˫���Բ�ֵ�㷨
    # ���Ҫ�޸����������ϵ����Ҫ�޸�dstSRS����ֵ��ʹ�ø�����ϵͳ��EPSG����
    # ��������ַhttps://spatialreference.org/ref/epsg/32650/  ��ѯ�õ�EPSG����


    
    # os.environ['GDAL_DATA'] = r'E:\ProgramData\Anaconda3\envs\gf\Library\share'

    write_rpc_to_tiff(inputpath,ap = True,outpath = None)
    print('��ʼͶӰ')
    if dem_tif_file is None:
        wo = gdal.WarpOptions(srcNodata=0, dstNodata=0, dstSRS='EPSG:4326', resampleAlg='bilinear',format='Gtiff',rpc=True, warpOptions=["INIT_DEST=NO_DATA"])
        
        wr = gdal.Warp(corrtiff,  inputpath, options=wo) 
        print("RPC_GEOcorr>>>")
    else:
        wo = gdal.WarpOptions(srcNodata=0, dstNodata=0, dstSRS='EPSG:4326', resampleAlg='bilinear', format='ENVI',rpc=True, warpOptions=["INIT_DEST=NO_DATA"],
                 transformerOptions=["RPC_DEM=%s"%(dem_tif_file), "RPC_DEMINTERPOLATION=bilinear"])     
        wr = gdal.Warp(corrtiff,  inputpath,  format='GTiff',dstSRS='EPSG:4326',resampleAlg='bilinear',rpc=True, warpOptions=["INIT_DEST=NO_DATA"])   
        print("RPC_GEOcorr>>>")
    ## ����ȫ�����Ӱ����߲�ʹ��DEMУ���Ļ������Խ�transformerOptions�йص�RPC DEM�ؼ���ɾ��
    ## ��������gdal.WarpOptionsע�͵�������������ȡ��ע�ͣ���DEMʱ��Ӱ��Χ�ĸ߳�Ĭ��ȫΪ0
    del wr

#����projĿ¼ ��Ҫ����"sat"
os.environ['PROJ_LIB'] = r'E:\ProgramData\Anaconda3\envs\sat\Library\share\proj'
#����1
    #�����ļ� ��Ҫע���׺Ϊ.tiff  ��rpb�ļ�ҲҪ�������ļ�������Ŀ¼��
    # eg:
    # r'E:\GF1_PMS2_E106.9_N29.1_20170212_L1A0002181816-MSS2.tiff'
#����2
    #����ļ�
    # eg:
    # r'E:\sss4.tiff'
rpc_correction('E:\GF1_PMS2_E106.9_N29.1_20170212_L1A0002181816-MSS2.tiff',r'E:\GF1_PMS2_E106.9_N29.1_20170212_L1A0002181816\sss4.tiff')
