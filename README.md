# trip-advisor-script
Crawler for TripAdvisor

Crawler for TripAdvisor

Hi all, I need an application in nodejs that is capable of
1) Open the tripadvisor site
2) Select one of the sections of the website (hotel, restaurant, etc etc) (this value is dinamic, need to pass when call application)
3) In the filter insert the region / city (this value is dinamic, need to pass when call application)
4) Search result
5) Open each result (like open each restaurant) and save all informations, to be precise:
Business name, address, all the images in the gallery (saved in base64, contacts (telephone, website, etc), type of cuisine, details
6) Save all this information in the database, you will need to create the structure of the databaes and share it with me before starting,
there will be dedicated tables such as address, photographs, contacts, etc.

The script will finish when it has saved all the restaurants of the selected region in the database.

Important: if you call it twice, the script will have to update the structure and not create a duplicate.
