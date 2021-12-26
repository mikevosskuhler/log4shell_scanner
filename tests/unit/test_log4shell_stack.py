import aws_cdk as core
import aws_cdk.assertions as assertions

from log4shell.log4shell_stack import Log4ShellStack

# example tests. To run these tests, uncomment this file along with the example
# resource in log4shell/log4shell_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Log4ShellStack(app, "log4shell")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
