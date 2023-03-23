# Dollar cost averaging bot with XTB API

This code combined with AWS lambda function allows you to automate the regular purchase of selected stocks. It uses xAPIConnector script provided by XTB for managing API subscriptions and messages. 

Requirements:
- XTB account (preferably demo account for testing),
- AWS account.

## 1. AWS SES activation

To enable sending email notifications you need to configure AWS Simple Email Services. AWS provides 62k free e-mails per month which is more than enough for this project.

To configure AWS Simple Email Services you need to:

1. Go to SES dashboard (type "SES" in AWS serachbox).
2. Click create identity, select "Email address" and fill email address that you want to use.
3. Click activation link in your mail inbox.

## 2. Creating lambda function

Lambda function is going to let you run your code automatically with close to 100% effectiveness. 

To create lambda function you have to:

1. Download code_to_upload.zip file from this repository. 
2. Go to AWS Lambda dashboard and click "Create new function"
3. Choose "Author from scratch", fill in function name, select Python 3.9 as runtime and x86_64 as architecture. Click "Create function".
4. You should see 'Code source' window. Click "Upload from", select ".zip file" and upload file you downloaded earlier.
5. Uploaded files should be visible in directory tree on the left side.

## 3. Modifying permissions policy

To let your lambda function send emails you need to modify its set of permissions. 

To do so you have to:

1. In SES dashboard side navbar click "verified identities" and then choose identity we've created earlier.
2. Copy Amazon Resource Name (ARN).
3. Go to IAM dashboard (type "IAM" in AWS serachbox).
4. Select "Roles" from side navbar.
5. Select role related to your lambda function name.
6. Edit permission policy JSON by adding to "Statement" list following code:

```
{
  "Effect": "Allow",
  "Action": [
      "ses:SendEmail",    
      "ses:SendRawEmail"
  ],
  "Resource": "paste-copied-ARN-here"
}
```

## 4. Changing timeout value

All AWS lambda functions' timeout is set to 3 s by default. Execution of this script may take around 10 s. In order to let your script execute properly you have to change timeout setting. To do so you need to:

1. Go to 'Configuration' tab in your lambda function dashboard.
2. Click 'Edit' in 'General configuration' window.
3. Set Timeout to 15 s. 
4. Click 'Save'.

## 5. Config.json

Before you run lambda function you have to fill in config.json file. It contains all necessary data for script to run. 

`username` - it's ID of an XTB account that you want to use. You can find account ID in top-right corner in xStation.

`password` - your XTB account password. 

`from_mail` - E-mail address you will be getting notifications from. Use the e-mail you activated during SES configuration.

`to_mail` - E-mail address you will be getting notifications to. You can use the same value as `from_mail`.

`balance_required` - minimum balance of your account required for script to run. 

`shopping_list` - list of stocks' tickers you want to buy with percentage of your balance you want to spend on each. 

***Sum of percentages cannot be greater than 100. Tickers of stocks which are provided by XTB as both CFDs and physical shares must contain _9 suffix. E.g. AAPL.US_9.***

After you filled config file click 'deploy' in the 'Source code' window. You have to deploy your code everytime you make changes in config file. 

## 6. Test your Lambda function

 Once you have done all the steps above you can test the lambda function. To do so you have to click blue Test button. When you click it for the first time you will have to configure test event. All you have to do is fill in Event name e.g. 'test'. If test was successful you should see "Execution successful" in Execution result tab and notification in your e-mail inbox. 
 
 ***It is highly recommended to use demo account at this phase. Balance refresh takes up to 10 minutes. You may encounter irregularities if you run script with shorter intervals.***
 
## 7. Setting trigger

After running test successfully you can set trigger which will run your script regularly. 

To do so you have to:

1. Click 'Configuration' tab in function dashboard.
2. Select 'triggers' from side navbar and click 'Add trigger'.
3. Select 'EventBridge (CloudWatch Events)'
4. Select 'Create a new rule'.
5. Fill in Rule name, select 'Schedule expression' and write cron expression in Schedule expression textbox. You can use cron expression generator like https://crontab.cronhub.io/ 

When writing cron expression take into consideration that no transaction will be made if market for at least one stock is closed at a time of script execution. 



