# About

Python scripts which check <a href="https://www.footlocker.it/"><b>footlocker</b></a> order status. For every order, the script sends a Discord webhook to notify the user about the status of the order. Finally, a summary file containing all orders information is generated.

# Libraries

<ul>
    <li>requests;</li>
    <li>json;</li>
    <li>random;</li>
    <li>csv;</li>
    <li>time;</li>
    <li>threading;</li>
    <li>datetime;</li>
    <li>bs4;</li>
    <li>discord_webhook;</li>
</ul>

# How to set up

Add your discord webhook to line <b>75</b>. Add your order number to "orders.csv" and run the script using "python 'cop_house_ftl_order_checker.py'" command on your terminal.

# Suggestion

In order to avoid ban from the site, the user can use proxy but simply adding them in "proxies.txt".
