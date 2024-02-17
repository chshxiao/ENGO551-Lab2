# ENGO551-Lab2

Lab 2 is a book searching and review web application with api.
Lab 2 is very similar to Lab 1 in many pages. Sign in, sign out, register page, and the main page are the same. You are not able to register a same user id, and the searching enables similar matching.

The new things of Lab2 starts from detail page. In detail page, average rating and reviews are added. Average rating is a data extracted from google book api and reviews are input by the users of the web application and are stored in reviews table in local database. The old published date feature from csv file is replaced by a coalesed published date. The coalesed published date is the published date from google book api if it's available, otherwise the published date from csv.

You can also click on the write a review link to write a review. Each user is only allowed to write one review on each book.

The web application also has its own api. The addess is /api/book/isbn/. You will get the following features:
title, ISBN10, ISBN13, author, published date, average rating, and review count. It returns in JSON format.
The website will output the 404 status code if you enter a unfound isbn.