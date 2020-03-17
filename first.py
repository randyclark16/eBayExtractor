# import ebaysdk
# from ebaysdk import finding

# api = finding(siteid='EBAY-GB', appid='<REPLACE WITH YOUR OWN APPID>')

# api.execute('findItemsAdvanced', {
#     'keywords': 'laptop',
#     'categoryId' : ['177', '111422'],
#     'itemFilter': [
#         {'name': 'Condition', 'value': 'Used'},
#         {'name': 'MinPrice', 'value': '200', 'paramName': 'Currency', 'paramValue': 'GBP'},
#         {'name': 'MaxPrice', 'value': '400', 'paramName': 'Currency', 'paramValue': 'GBP'}
#     ],
#     'paginationInput': {
#         'entriesPerPage': '25',
#         'pageNumber': '1' 	 
#     },
#     'sortOrder': 'CurrentPriceHighest'
# })

# dictstr = api.response_dict()



from ebaysdk.exception import ConnectionError
from ebaysdk.finding import Connection
import datetime
import json
from azure.servicebus import QueueClient, Message

def CreateItemDictionary(response_item):
    """
    Create a structurally identical copy of a response.reply.searchResult.item dictionary.

    For some reason all parts of the response object returned from the ebaysdk are read-only and non-serializable so we cannot
    convert them to a string to be used to create a Message for the Service Bus. This function goes node by node and creates a
    structurally identical copy that CAN be serialized to a string so we can create a Message.

    Parameters:
    response_item (dict): The response.reply.searchResult.item dictionary that is protected and cannot be serialized

    Returns:
    dict: A copy of the response.reply.searchResult.item as a plain python dictionary that can be serialized  

    """
    # Example of Response Item structure
    # {
    #     "itemId": "282724539256",
    #     "title": "LEGO Star Wars Snow Speeder 75049 Brand new Factory Sealed",
    #     "globalId": "EBAY-US",
    #     "primaryCategory": {
    #         "categoryId": "19006",
    #         "categoryName": "LEGO Complete Sets & Packs"
    #     },
    #     "galleryURL": "https://thumbs1.ebaystatic.com/m/mkG8wJuQWPJ-r-WN_JYuVRA/140.jpg",
    #     "viewItemURL": "https://www.ebay.com/itm/LEGO-Star-Wars-Snow-Speeder-75049-Brand-new-Factory-Sealed-/282724539256",
    #     "paymentMethod": "PayPal",
    #     "autoPay": "false",
    #     "postalCode": "077**",
    #     "location": "Englishtown,NJ,USA",
    #     "country": "US",
    #     "shippingInfo": {
    #         "shippingServiceCost": {
    #             "_currencyId": "USD",
    #             "value": "0.0"
    #         },
    #         "shippingType": "Free",
    #         "shipToLocations": "Worldwide",
    #         "expeditedShipping": "true",
    #         "oneDayShippingAvailable": "false",
    #         "handlingTime": "1"
    #     },
    #     "sellingStatus": {
    #         "currentPrice": {
    #             "_currencyId": "USD",
    #             "value": "199.88"
    #         },
    #         "convertedCurrentPrice": {
    #             "_currencyId": "USD",
    #             "value": "199.88"
    #         },
    #         "sellingState": "Active",
    #         "timeLeft": "P26DT12H31M37S"
    #     },
    #     "listingInfo": {
    #         "bestOfferEnabled": "false",
    #         "buyItNowAvailable": "false",
    #         "startTime": datetime.datetime(2017,11,7,13,20,55),
    #         "endTime": datetime.datetime(2020,3,7,13,20,55),
    #         "listingType": "StoreInventory",
    #         "gift": "false"
    #     },
    #     "returnsAccepted": "true",
    #     "condition": {
    #         "conditionId": "1000",
    #         "conditionDisplayName": "New"
    #     },
    #     "isMultiVariationListing": "false",
    #     "topRatedListing": "true"
    # }
 
    item_dict = {}
    item_dict["itemId"] = response_item.get("itemId")
    item_dict["title"] = response_item.get("title")
    item_dict["globalId"] = response_item.get("globalId")
 
    primaryCategory = response_item.get("primaryCategory")
    if primaryCategory:
        item_dict["primaryCategory"] = {}
        item_dict["primaryCategory"]["categoryId"] = primaryCategory.get("categoryId")
        item_dict["primaryCategory"]["categoryName"] = primaryCategory.get("categoryName")

    item_dict["galleryURL"] = response_item.get("galleryURL")
    item_dict["viewItemURL"] = response_item.get("viewItemURL")
    item_dict["paymentMethod"] = response_item.get("paymentMethod")
    item_dict["autoPay"] = response_item.get("autoPay")
    item_dict["postalCode"] = response_item.get("postalCode")
    item_dict["location"] = response_item.get("location")
    item_dict["country"] = response_item.get("country")    

    shippingInfo = response_item.get("shippingInfo")
    if shippingInfo:
        item_dict["shippingInfo"] = {}
        shippingServiceCost = shippingInfo.get("shippingServiceCost")
        if shippingServiceCost:
            item_dict["shippingInfo"]["shippingServiceCost"] = {}
            item_dict["shippingInfo"]["shippingServiceCost"]["_currencyId"] = shippingInfo.get("_currencyId")
            item_dict["shippingInfo"]["shippingServiceCost"]["value"] = shippingInfo.get("value")

        item_dict["shippingInfo"]["shippingType"] = shippingInfo.get("shippingType")
        item_dict["shippingInfo"]["shipToLocations"] = shippingInfo.get("shipToLocations")
        item_dict["shippingInfo"]["expeditedShipping"] = shippingInfo.get("expeditedShipping")
        item_dict["shippingInfo"]["oneDayShippingAvailable"] = shippingInfo.get("oneDayShippingAvailable")
        item_dict["shippingInfo"]["handlingTime"] = shippingInfo.get("handlingTime")

    sellingStatus = response_item.get("sellingStatus")
    if sellingStatus:
        item_dict["sellingStatus"] = {}
        item_dict["sellingStatus"]["sellingState"] = sellingStatus.get("sellingState")
        item_dict["sellingStatus"]["timeLeft"] = sellingStatus.get("timeLeft")
 
    listingInfo = response_item.get("listingInfo")
    if listingInfo:
        item_dict["listingInfo"] = {}
        item_dict["listingInfo"]["bestOfferEnabled"] = listingInfo.get("bestOfferEnabled")
        item_dict["listingInfo"]["buyItNowAvailable"] = listingInfo.get("buyItNowAvailable")
        item_dict["listingInfo"]["startTime"] = listingInfo.get("startTime").isoformat()
        item_dict["listingInfo"]["endTime"] = listingInfo.get("endTime").isoformat()
        item_dict["listingInfo"]["listingType"] = listingInfo.get("listingType")
        item_dict["listingInfo"]["gift"] = listingInfo.get("gift")      
 
    item_dict["returnsAccepted"] = response_item.get("returnsAccepted")
 
    condition = response_item.get("condition")
    if condition:
        item_dict["condition"] = {}
        item_dict["condition"]["conditionId"] = condition.get("conditionId")
        item_dict["condition"]["conditionDisplayName"] = condition.get("conditionDisplayName")
   
    item_dict["isMultiVariationListing"] = response_item.get("isMultiVariationListing")
    item_dict["topRatedListing"] = response_item.get("topRatedListing")
 
    return item_dict
 


try:
    with open ('local.settings.json') as f:
        settings = json.load(f)
    service_bus_connect_string = settings.get("serviceBusConnectString")
    randy_appid = settings.get("randyAppid")
    api = Connection(appid='RandyCla-Activity-PRD-b82249abe-e4baca6b ', config_file=None)
    response = api.execute('findItemsAdvanced', {
        'keywords': 'lego snowspeeder 75049 Sealed',
        'sortOrder': 'CurrentPriceHighest',
        'paginationInput': {
            'entriesPerPage': '50',
            'pageNumber': '1' 
            }	 
        })

    assert(response.reply.ack == 'Success')
    assert(type(response.reply.timestamp) == datetime.datetime)
    assert(type(response.reply.searchResult.item) == list)

    queue_client = QueueClient.from_connection_string("Endpoint=sb://randyservicebus.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=xkdYx/eOfK5kaTqKnysRJn7bSuMew7qFt5pBJeOSbdU=", "ebayevents")

    item = response.reply.searchResult.item[0]
    assert(type(item.listingInfo.endTime) == datetime.datetime)
    assert(type(response.dict()) == dict)
    print("Number of Items: {}".format(len(response.reply.searchResult.item)))
    for item in response.reply.searchResult.item:
        item_id = item.get('itemId')
        title = item.get('title')
        primary_category = item.get('primaryCategory')
        if primary_category:
            category_id = primary_category.get('categoryId')
            category_name = primary_category.get('categoryName')
        else:
            category_id = "none"
            category_name = "none"

        print ("ItemID: {}".format(item_id)) 
        print ("Title: {}".format(title))
        print ("Category Name: {}, CategoryID: {}".format(category_name,category_id))
        print ("________________________________________________________")
        # We cannot serialize anything in a response object so copy the contents to a dict created from scratch
        each_item_copy = CreateItemDictionary(item)
        # Send the listing as a message to the service bus
        each_item_json_string = json.dumps(each_item_copy)
        message = Message(each_item_json_string)
        queue_client.send(message)

except ConnectionError as e:
    print(e)
    print(e.response.dict())

