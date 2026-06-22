# Wai-Badminton-Tracker

A lightweight web application designed to manage badminton sessions. Admin create sessions/users via the admin panel and then manage specific sessions via a central dashboard. It is built using **HTML**, **Django**, and **HTMX**.

Licensed under the **PolyForm Noncommercial License 1.0.0**.  
See [LICENSE](LICENSE) for details.

**This software is for non-commercial use only.**


---

## Getting Started

#### Deployment
See [DEPLOYMENT](DEPLOYMENT.md)


#### Import Players
Admins can import players from ebadders/ using the endpoints `{URL}/import-players/ebadders/` or `{URL}/import-players/superbadders/`

##### Ebadders

Under `https://ebadders.com/{YOUR_CLUB_NAME}/players?o=name` on Google Chrome, ctrl + S, Save as type `Web Page, HTML Only` and upload it to  `{URL}/import-players/ebadders/`


##### Superbadders

Under `https://www.superbadders.com/myplayers.php` > Backup/Export > , Copy to Clipboard and paste the string into  `{URL}/import-players/superbadders/`

 
---

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md)


