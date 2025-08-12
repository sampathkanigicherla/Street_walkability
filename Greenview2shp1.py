import os
from osgeo import ogr, osr


def Read_GSVinfo_Text(GVI_Res_txt):
    """
    Reads a single GVI result text file, extracts relevant GSV info, and returns data lists.
    Filters out invalid or duplicate records.
    """
    panoIDLst = []
    panoDateLst = []
    panoLonLst = []
    panoLatLst = []
    greenViewLst = []

    with open(GVI_Res_txt, "r", encoding="utf-8") as lines:
        for line in lines:
            if "panoDate" not in line or "greenview" not in line:
                continue

            panoID = line.split(" panoDate")[0][-22:]
            panoDate = line.split(" longitude")[0][-7:]
            coordinate = line.split("longitude: ")[1]
            lon = coordinate.split(" latitude: ")[0]
            latView = coordinate.split(" latitude: ")[1]
            lat = latView.split(', greenview:')[0]
            greenView = line.split("greenview:")[1].strip()

            if not greenView or len(greenView) < 2:
                continue
            try:
                greenViewFloat = float(greenView)
                if greenViewFloat < 0:
                    continue
            except ValueError:
                continue

            if panoID not in panoIDLst:
                panoIDLst.append(panoID)
                panoDateLst.append(panoDate)
                panoLonLst.append(lon)
                panoLatLst.append(lat)
                greenViewLst.append(greenView)

    return panoIDLst, panoDateLst, panoLonLst, panoLatLst, greenViewLst


def Read_GVI_res(GVI_Res):
    """
    Reads either a folder of GVI result text files or a single file, aggregates results.
    """
    panoIDLst = []
    panoDateLst = []
    panoLonLst = []
    panoLatLst = []
    greenViewLst = []

    if os.path.isdir(GVI_Res):
        allTxtFiles = os.listdir(GVI_Res)
        for txtfile in allTxtFiles:
            if not txtfile.endswith('.txt'):
                continue
            txtfilename = os.path.join(GVI_Res, txtfile)
            panoID_tem, panoDate_tem, lon_tem, lat_tem, gvi_tem = Read_GSVinfo_Text(txtfilename)
            panoIDLst += panoID_tem
            panoDateLst += panoDate_tem
            panoLonLst += lon_tem
            panoLatLst += lat_tem
            greenViewLst += gvi_tem
    else:
        panoID_tem, panoDate_tem, lon_tem, lat_tem, gvi_tem = Read_GSVinfo_Text(GVI_Res)
        panoIDLst += panoID_tem
        panoDateLst += panoDate_tem
        panoLonLst += lon_tem
        panoLatLst += lat_tem
        greenViewLst += gvi_tem

    return panoIDLst, panoDateLst, panoLonLst, panoLatLst, greenViewLst


def CreatePointFeature_ogr(outputShapefile, LonLst, LatLst, panoIDlist, panoDateList, greenViewList, lyrname):
    """
    Creates a point shapefile from provided lists with fields: panoID, panoDate, greenView.
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")

    if os.path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)

    data_source = driver.CreateDataSource(outputShapefile)
    targetSpatialRef = osr.SpatialReference()
    targetSpatialRef.ImportFromEPSG(4326)

    outLayer = data_source.CreateLayer(lyrname, targetSpatialRef, ogr.wkbPoint)

    numPnt = len(LonLst)
    print('The number of points is:', numPnt)

    if numPnt == 0:
        print('You created an empty shapefile')
        return

    # Define fields
    outLayer.CreateField(ogr.FieldDefn('PntNum', ogr.OFTInteger))
    outLayer.CreateField(ogr.FieldDefn('panoID', ogr.OFTString))
    outLayer.CreateField(ogr.FieldDefn('panoDate', ogr.OFTString))
    outLayer.CreateField(ogr.FieldDefn('greenView', ogr.OFTReal))

    for idx in range(numPnt):
        if len(LonLst[idx]) < 3:
            continue

        try:
            lon = float(LonLst[idx])
            lat = float(LatLst[idx])
            greenView = float(greenViewList[idx]) if greenViewList else -999
        except ValueError:
            continue

        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)

        featureDefn = outLayer.GetLayerDefn()
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(point)
        outFeature.SetField('PntNum', idx)
        outFeature.SetField('panoID', panoIDlist[idx])
        outFeature.SetField('panoDate', panoDateList[idx])
        outFeature.SetField('greenView', greenView)

        outLayer.CreateFeature(outFeature)
        outFeature = None  # Proper cleanup

    data_source = None  # Final cleanup


# ---------------------- MAIN EXECUTION ---------------------- #
if __name__ == "__main__":
    inputGVIres = r'C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\green_view_index'
    outputShapefile = r'C:\Treepedia_Public-master\india_city_shapefiles\Nellore\shape\Green_view_shape_file'
    lyrname = 'greenView'

    panoIDlist, panoDateList, LonLst, LatLst, greenViewList = Read_GVI_res(inputGVIres)
    print('The length of the panoIDList is:', len(panoIDlist))

    CreatePointFeature_ogr(outputShapefile, LonLst, LatLst, panoIDlist, panoDateList, greenViewList, lyrname)

    print('Done!!!')