def createRouteSumoFile(pathFileRoute,startRoute,endRoute="24884052#0"):
    xmlPatternRoute='<?xml version="1.0" encoding="UTF-8"?>'+'\n'
    xmlPatternRoute=xmlPatternRoute+'<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">'+'\n'
    xmlPatternRoute=xmlPatternRoute+'<vType id="vType_0" vClass="passenger" maxSpeed="20" decel="20" color="255,255,0" length="0.5"/>' +'\n'
    xmlPatternRoute = xmlPatternRoute + '<vType id="routeByDistance" maxSpeed="1" color="0,255,255"/>' + '\n'
    xmlPatternRoute=xmlPatternRoute+'<route id="r_0" edges="'+startRoute+' '+endRoute+'"  />'+'\n'
    xmlPatternRoute= xmlPatternRoute+'</routes>'
    with open(pathFileRoute, 'w+') as f:
        f.write(xmlPatternRoute)
        f.close()