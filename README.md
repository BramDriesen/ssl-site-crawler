# SSL Site Crawler

An ethical crawler bot to create a safer internet for everyone.

As of July 2018, Google ([read][1]) is going to start prominently telling its users that the sites they’re visiting aren not secure. To combat this issue and create a safer internet for everyone I decided to create a scraper that will try to scrape all _government_* websites and check if they are correctly protected with an SSL certificate.

\* Or other sites matching the search criteria/force include setup. 

All the data will be stored in a Firebase database to later on sanitize the data and create some infographics.

## Setup
TODO

## Firebase setup
Source: https://firebase.google.com/docs/admin/setup

1. If you don't already have a Firebase project, add one in the Firebase console. The Add project dialog also gives you the option to add Firebase to an existing Google Cloud Platform project.
2. Navigate to the Service Accounts tab in your project's settings page.
3. Click the Generate New Private Key button at the bottom of the Firebase Admin SDK section of the Service Accounts tab.



## Q&A

**Q: Are Python 1 & 2 supported?**  
A: Nope

**Q: How is the performance like?**  
A: Not that great imho especially if you use the Google search. Nevertheless the performance is depending on a lot of different variables, like: How fast can Google return the results, how fast is the target website, how fast is my data transfer to Firebase, how fast is my own internet connection,...

**Q: When is a site marked as unsafe?**  
A: I decided to mark a a website as unsafe when any of the following criteria are met:
* No HTTPS available
* HTTPS enabled websites that don't automatically redirect HTTP to HTTPS 
* Invalid certificates or other certificate errors

If google happens to return a dead URL, the URL is marked as 'dead'.

**Q: Should all websites have an SSL certificate?**  
A: In my opinion, YES!

**Q: SSL Certificates are expensive, I don't want to spend X$ for my small website. What should I do?**  
A: Take a look at [letsencrypt][2], they offer free SSL certificates for everyone. Furthermore more and more hosting providers are providing Let's encrypt for free in their offerings. 

**Q: Should I care about SSL certificates?**  
A: Yes you should! From the moment your website has a login form, or any other form. Hackers can intercept the communication between the user and your back-end system. If your website is not encrypted it's like writing your PIN code on your credit card and giving it to a stranger.

**Q: Is this the best way to crawl websites based on keywords?**  
A: Probably not, but it works fine in my use case.

[1]: https://security.googleblog.com/2018/02/a-secure-web-is-here-to-stay.html
[2]: https://letsencrypt.org