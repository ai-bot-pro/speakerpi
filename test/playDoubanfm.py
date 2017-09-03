import os
for i in range(0,100):
    url = os.popen("curl -b 'bid=ha5ZoPgYmgM; flag=ok; ac=1504322797; dbcl2=3867696:fVfJ9GW24NM; ck=Mz4D;' 'https://douban.fm/j/v2/playlist?channel=0&kbps=128&client=s%3Amainsite%7Cy%3A3.0&app_name=radio_website&version=100&type=r&sid=2145476&pt=&pb=128&apikey=' | jq .song[0].url").readline()
    print("mplayer "+url)
    os.system("mplayer "+url)
