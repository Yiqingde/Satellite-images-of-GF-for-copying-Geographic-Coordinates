# 给高分系列卫星影像添加地理坐标
问题陈述:两张高分影像。影像A：具有地理坐标信息XML；影像B:不具备地理坐标信息。将影像A的地理信息赋给影像B。
应用的场景：图像mask标签无地理坐标，有原始图像，对mask赋值。
CSDN Blog:https://blog.csdn.net/weixin_42348202/
# Adding Geographic Coordinates to GF Satellite Images Problem Statement:
Two High Score Images. Image A: XML with geographic coordinate information; Image B: does not have geographic coordinate information. Assign the geographic information of image A to image B. 
Application scenario: The image mask tag has no geographical coordinates, but has an original image, and the mask is assigned a value.
CSDN Blog:https://blog.csdn.net/weixin_42348202/
## addpos-v1.py

```python import os
import sys


from threading import currentThread
import numpy as np



# from Py6S import *
from osgeo import gdal,gdal_array



def parse_rpc_file(rpc_file):
    # rpc_file:.rpc文件的绝对路径
    # rpc_dict：符号RPC域下的16个关键字的字典
    # 参考网址：http://geotiff.maptools.org/rpc_prop.html；
    # https://www.osgeo.cn/gdal/development/rfc/rfc22_rpc.html
 
    rpc_dict = {}
    with open(rpc_file) as f:
        text = f.read()
 
    # .rpc文件中的RPC关键词
    words = ['errBias', 'errRand', 'lineOffset', 'sampOffset', 'latOffset',
             'longOffset', 'heightOffset', 'lineScale', 'sampScale', 'latScale',
             'longScale', 'heightScale', 'lineNumCoef', 'lineDenCoef','sampNumCoef', 'sampDenCoef',]
 
    # GDAL库对应的RPC关键词
    keys = ['ERR_BIAS', 'ERR_RAND', 'LINE_OFF', 'SAMP_OFF', 'LAT_OFF', 'LONG_OFF',
            'HEIGHT_OFF', 'LINE_SCALE', 'SAMP_SCALE', 'LAT_SCALE',
            'LONG_SCALE', 'HEIGHT_SCALE', 'LINE_NUM_COEFF', 'LINE_DEN_COEFF',
            'SAMP_NUM_COEFF', 'SAMP_DEN_COEFF']
 
    for old, new in zip(words, keys):
        text = text.replace(old, new)
    # 以‘;\n’作为分隔符
    text_list = text.split(';\n')
    # 删掉无用的行
    text_list = text_list[3:-2]
    #
    text_list[0] = text_list[0].split('\n')[1]
    # 去掉制表符、换行符、空格
    text_list = [item.strip('\t').replace('\n', '').replace(' ', '') for item in text_list]
 
    for item in text_list:
        # 去掉‘=’
        key, value = item.split('=')
        # 去掉多余的括号‘(’，‘)’
        if '(' in value:
            value = value.replace('(', '').replace(')', '')
        rpc_dict[key] = value
 
    for key in keys[:12]:
        # 为正数添加符号‘+’
        if not rpc_dict[key].startswith('-'):
            rpc_dict[key] = '+' + rpc_dict[key]
        # 为归一化项和误差标志添加单位
        if key in ['LAT_OFF', 'LONG_OFF', 'LAT_SCALE', 'LONG_SCALE']:
            rpc_dict[key] = rpc_dict[key] + ' degrees'
        if key in ['LINE_OFF', 'SAMP_OFF', 'LINE_SCALE', 'SAMP_SCALE']:
            rpc_dict[key] = rpc_dict[key] + ' pixels'
        if key in ['ERR_BIAS', 'ERR_RAND', 'HEIGHT_OFF', 'HEIGHT_SCALE']:
            rpc_dict[key] = rpc_dict[key] + ' meters'
 
    # 处理有理函数项
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
        # 可修改读取
        dataset = gdal.Open(inputpath,gdal.GA_Update)
        # 向tif影像写入rpc域信息
        # 注意，这里虽然写入了RPC域信息，但实际影像还没有进行实际的RPC校正
        # 尽管有些RS/GIS能加载RPC域信息，并进行动态校正
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
    #输入路径 输出路径 de m
    ## 设置rpc校正的参数
    # 原图像和输出影像缺失值设置为0，输出影像坐标系为WGS84(EPSG:4326), 重采样方法为双线性插值（bilinear，还有最邻近‘near’、三次卷积‘cubic’等可选)
    # 注意DEM的覆盖范围要比原影像的范围大，此外，DEM不能有缺失值，有缺失值会报错
    # 通常DEM在水域是没有值的（即缺失值的情况），因此需要将其填充设置为0，否则在RPC校正时会报错
    # 这里使用的DEM是填充0值后的SRTM V4.1 3秒弧度的DEM(分辨率为90m)
    # RPC_DEMINTERPOLATION=bilinear  表示对DEM重采样使用双线性插值算法
    # 如果要修改输出的坐标系，则要修改dstSRS参数值，使用该坐标系统的EPSG代码
    # 可以在网址https://spatialreference.org/ref/epsg/32650/  查询得到EPSG代码


    
    # os.environ['GDAL_DATA'] = r'E:\ProgramData\Anaconda3\envs\gf\Library\share'

    write_rpc_to_tiff(inputpath,ap = True,outpath = None)
    print('开始投影')
    if dem_tif_file is None:
        wo = gdal.WarpOptions(srcNodata=0, dstNodata=0, dstSRS='EPSG:4326', resampleAlg='bilinear',format='Gtiff',rpc=True, warpOptions=["INIT_DEST=NO_DATA"])
        
        wr = gdal.Warp(corrtiff,  inputpath, options=wo) 
        print("RPC_GEOcorr>>>")
    else:
        wo = gdal.WarpOptions(srcNodata=0, dstNodata=0, dstSRS='EPSG:4326', resampleAlg='bilinear', format='ENVI',rpc=True, warpOptions=["INIT_DEST=NO_DATA"],
                 transformerOptions=["RPC_DEM=%s"%(dem_tif_file), "RPC_DEMINTERPOLATION=bilinear"])     
        wr = gdal.Warp(corrtiff,  inputpath,  format='GTiff',dstSRS='EPSG:4326',resampleAlg='bilinear',rpc=True, warpOptions=["INIT_DEST=NO_DATA"])   
        print("RPC_GEOcorr>>>")
    ## 对于全海域的影像或者不使用DEM校正的话，可以将transformerOptions有关的RPC DEM关键字删掉
    ## 即将上面gdal.WarpOptions注释掉，将下面的语句取消注释，无DEM时，影像范围的高程默认全为0
    del wr

#设置proj目录 主要更改"sat"
os.environ['PROJ_LIB'] = r'E:\ProgramData\Anaconda3\envs\sat\Library\share\proj'
#参数1
    #输入文件 需要注意后缀为.tiff  。rpb文件也要在输入文件夹所在目录中
    # eg:
    # r'E:\GF1_PMS2_E106.9_N29.1_20170212_L1A0002181816-MSS2.tiff'
#参数2
    #输出文件
    # eg:
    # r'E:\sss4.tiff'
rpc_correction('E:\GF1_PMS2_E106.9_N29.1_20170212_L1A0002181816-MSS2.tiff',r'E:\GF1_PMS2_E106.9_N29.1_20170212_L1A0002181816\sss4.tiff')
```
