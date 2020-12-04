from pymongo import MongoClient
import datetime

from geopy.geocoders import Nominatim


geolocator = Nominatim(user_agent="twint-1.2")

def getLocation(place, **options):
    location = geolocator.geocode(place,timeout=1000)
    if location:
        if options.get("near"):
            global _near
            _near = {"lat": location.latitude, "lon": location.longitude}
            return True
        elif options.get("location"):
            global _location
            _location = {"lat": location.latitude, "lon": location.longitude}
            return True
        return {"lat": location.latitude, "lon": location.longitude}
    else:
        return {}

def Tweet(Tweet, config):
    global _index_tweet_status
    global _is_near_def
    date_obj = datetime.strptime(Tweet.datetime, "%Y-%m-%d %H:%M:%S %Z")

    actions = []

    try:
        retweet = Tweet.retweet
    except AttributeError:
        retweet = None

    dt = f"{Tweet.datestamp} {Tweet.timestamp}"

    j_data = {
            "_index": config.Index_tweets,
            "_id": str(Tweet.id) + "_raw_" + config.Essid,
            "_source": {
                "id": str(Tweet.id),
                "conversation_id": Tweet.conversation_id,
                "created_at": Tweet.datetime,
                "date": dt,
                "timezone": Tweet.timezone,
                "place": Tweet.place,
                "tweet": Tweet.tweet,
                "language": Tweet.lang,
                "hashtags": Tweet.hashtags,
                "cashtags": Tweet.cashtags,
                "user_id_str": Tweet.user_id_str,
                "username": Tweet.username,
                "name": Tweet.name,
                "day": date_obj.weekday(),
                "hour": date_obj.hour,
                "link": Tweet.link,
                "retweet": retweet,
                "essid": config.Essid,
                "nlikes": int(Tweet.likes_count),
                "nreplies": int(Tweet.replies_count),
                "nretweets": int(Tweet.retweets_count),
                "quote_url": Tweet.quote_url,
                "video": Tweet.video,
                "search": str(config.Search),
                "near": config.Near
                }
            }
    if retweet is not None:
        j_data["_source"].update({"user_rt_id": Tweet.user_rt_id})
        j_data["_source"].update({"user_rt": Tweet.user_rt})
        j_data["_source"].update({"retweet_id": Tweet.retweet_id})
        j_data["_source"].update({"retweet_date": Tweet.retweet_date})
    if Tweet.reply_to:
        j_data["_source"].update({"reply_to": Tweet.reply_to})
    if Tweet.photos:
        _photos = []
        for photo in Tweet.photos:
            _photos.append(photo)
        j_data["_source"].update({"photos": _photos})
    if Tweet.thumbnail:
        j_data["_source"].update({"thumbnail": Tweet.thumbnail})
    if Tweet.mentions:
        _mentions = []
        for mention in Tweet.mentions:
            _mentions.append(mention)
        j_data["_source"].update({"mentions": _mentions})
    if Tweet.urls:
        _urls = []
        for url in Tweet.urls:
            _urls.append(url)
        j_data["_source"].update({"urls": _urls})
    if config.Near or config.Geo:
        if not _is_near_def:
            __geo = ""
            __near = ""
            if config.Geo:
                __geo = config.Geo
            if config.Near:
                __near = config.Near
            _is_near_def = getLocation(__near + __geo, near=True)
        if _near:
            j_data["_source"].update({"geo_near": _near})
    if Tweet.place:
        _t_place = getLocation(Tweet.place)
        if _t_place:
            j_data["_source"].update({"geo_tweet": getLocation(Tweet.place)})
    if Tweet.source:
        j_data["_source"].update({"source": Tweet.Source})
    if config.Translate:
        j_data["_source"].update({"translate": Tweet.translate})
        j_data["_source"].update({"trans_src": Tweet.trans_src})
        j_data["_source"].update({"trans_dest": Tweet.trans_dest})

    actions.append(j_data)

    # es = Elasticsearch(config.Elasticsearch, verify_certs=config.Skip_certs)
    # if not _index_tweet_status:
    #     _index_tweet_status = createIndex(config, es, scope="tweet")
    # with nostdout():
    #     helpers.bulk(es, actions, chunk_size=2000, request_timeout=200)
    # actions = []

    client = MongoClient(config.MongoDB.url)
    db = client[config.MongoDB.db]
    collection = db[config.MongoDB.collection]
    collection.insert_one(actions)
    client.close()