# Wai-Badminton-Tracker

<p align="center">
WBT is a lightweight web application focused primarily on manage sessions for your badminton club. Built primarily using <strong>HTML</strong>, <strong>Django</strong>, and <strong>HTMX</strong>.

<br>

<img src="./images/wai-badminton-tracker.png" alt="wai-badminton-tracker">

</p>



| Feature | eBadders | SuperBadders | WBT |
|---|---|---|---|
| Court management | ✅ | ✅ | ✅ |
| Automatic player matching | ✅ | ✅ | ✅ |
| Adjust player strength | ❌ | ⚠️ | ✅ |
| Player pairing system | ✅ | ⚠️ | ✅ |
| Multiple device support | ✅ | ❌ | ✅ |
| No internet | ❌ | ⚠️ | ❌ |
| Handles gender imbalance | ❌ | ✅ | ✅ |
| Modern web interface | ✅ | ❌ | ✅ |
| Control over your own data | ❌ | ✅ | ✅ |
| Session Summary | ✅ | ❌ | TBA |
| **Free forever** | ⚠️ | ⚠️ | ✅ |

## Getting Started

#### Deployment
See [DEPLOYMENT](DEPLOYMENT.md)


#### Import Players
Admins can import players from ebadders/ using the endpoints `{URL}/import-players/ebadders/` or `{URL}/import-players/superbadders/`

##### Ebadders
Under `https://ebadders.com/{YOUR_CLUB_NAME}/players?o=name` on Google Chrome, ctrl + S, Save as type `Web Page, HTML Only` and upload it to  `{URL}/import-players/ebadders/`


##### Superbadders
Under `https://www.superbadders.com/myplayers.php` > Backup/Export > , Copy to Clipboard and paste the string into  `{URL}/import-players/superbadders/`

 

## Contributing

Thank you for considering contributing! See [CONTRIBUTING](CONTRIBUTING.md)


## License

Licensed under the **PolyForm Noncommercial License 1.0.0**.  
See [LICENSE](LICENSE) for details.

**This software is for non-commercial use only.**

