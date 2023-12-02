# NYC Citibike Stations via SMS 

Text your current cross streets or address to 1-844-407-2201, and you will receive a response with the 3 closest Citibike stations and their bike/dock availability!
With a Citibike key and a dumb phone, you no longer need the Citibike app (or a smartphone)!


## Usage

Send your current address or cross streets in a format that Google Maps would understand, e.g.:
- `E 27 St and 1 Av Manhattan`
- `20 W 34 St Manhattan`
- `12 St and 37 Av Astoria`
- `Vanderbilt and Willoughby Brooklyn`
- `Bronx Zoo Asia Gate`

You will receive a text response like:
```
21 St & 38 Ave has 18 bikes, 0 e-bikes, 0 docks.
36 Ave & 10 St has 10 bikes, 2 e-bikes, 0 docks.
21 St & 36 Ave has 8 bikes, 0 e-bikes, 11 docks.
```

Yes, it requires a little knowledge of the streets around you. Just like the olden days.

## How It Works

Code Overview:
1. Google Maps geocoding API to return latitude/longitude of inputted address/cross streets
2. Pull live list of stations from Citibike feed
3. Calculate nearest stations to the inputted location
4. Check bike/dock availability at those nearby stations using Citibike feed

Infrastructure:
- Flask for the app
- Twilio for messaging
- PythonAnywhere for hosting
- MySQL for DB (your phone number is stored in the DB but it is secure and it's just to make sure no one is abusing this and costing me a lot of money!)

## Inspiration

- In an effort to reduce my screentime, I recently purchased a dumb phone to use outside of work. 
- As an avid Citibiker, I quickly realized knowing Citibike station availability was a crucial part of my smartphone.
- Fortunately, I happened to be wanting to build a full project on my own at the same time.
- So I developed this and solved my issue!

## Future Steps

- If you have any updates or ideas, let me know!
- For now, everything is totally free and I'm eating a small monthly cost. I assume that will continue—I can't imagine the citibikeNYC x dumbphones intersection is huge!
- If you live in another city with a bikeshare system (with a GBFS feed) and are interested in adding your city, let me know. Will do it if there's interest.
- I'm considering working on a similar project to get step-by-step directions via SMS, especially since Google Maps recently removed that native feature.
