# coding=UTF-8
from lib.builder import PBSBuilder
import datetime

builder = PBSBuilder() 

delivery_builder = builder.delivery(dataSupplCVR=66357317,creditorPbsNumber=2408503)

section_builder = delivery_builder.payment_section(internalUserID="Members",
                                                   creditorBankReg=9001,
                                                   creditorBankAcct=9001123456,
                                                   mainTextLine="Membership Fee 2010")

section_builder.due_automatic_payment(customerId=767,
                                      agreementId=889988991,
                                      dueDate=datetime.datetime(2010,11,1),
                                      amount=15000)

section_builder.text(u"Fee for your membership of FøøOrg East");

section_builder.due_automatic_payment(customerId=556,
                                      agreementId=998899881,
                                      dueDate=datetime.datetime(2010,11,1),
                                      amount=7500)

section_builder.text("Fee for your membership of FooOrg West");

delivery_builder.append(section_builder.build())

delivery_builder.build()
delivery_builder.write_file("pbs-file.bs1")

print "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
print "        10        20        30        40        50        60        70        80        90       100       100       120       130"
for rec in delivery_builder.all_records():
    print rec.generate_line()+"."
