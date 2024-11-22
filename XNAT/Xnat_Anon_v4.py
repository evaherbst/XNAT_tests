import pandas as pd
import os
import csv
import numpy as np

# DISCLAIMER: the creators of this script are not responsible for any anonymisation or failure to anonymise using this script
# failure can occur for various reasons including small typos or retired tags and other reasons listed in the resources below


# We will use the tags defined by the DICOM standard as possibly having confidential info
# We use DICOM NEMA Table E.1-1. "Application Level Confidentiality Profile Attributes" PS3.15 2024d
# link: https://dicom.nema.org/medical/dicom/current/output/chtml/part15/chapter_E.html
# However, this table does not contain VR (data type) so we need to combine it with another table that does: 
# We use DICOM NEMA Table 6-1. "Registry of DICOM Data Elements" PS3.6 2024d 
# link: https://dicom.nema.org/medical/dicom/current/output/chtml/part06/chapter_6.html
 

# myFolder = "C:/Users/maxmo/"
myFolder = "C:/Users/eherbst/git/xnat/Eva_tests/"
allTags_fileName = "DicomStandard_Nema_AllTags_PS3_6_2024d.csv"
phiTags_fileName = "DicomStandard_Nema_PS3_15_2024d_E_Application_Level_Confidentiality_Profile_Attributes.csv"


df = pd.read_csv(os.path.join(myFolder, allTags_fileName))
df_PHI_tags = pd.read_csv(os.path.join(myFolder, phiTags_fileName))

df_PHI_tags = df_PHI_tags.iloc[:, 0:5] # selects columns from index 0 to 4 (the 0:5 range is exclusive at the end, so it keeps columns 0 through 4).

# check if any tags in the PHI tag table that are not in allTags list
missing_tags = set(df_PHI_tags ["Tag"]) - set(df["Tag"])

# Filter df_B for rows with these missing tags
missing_tags_df = df_PHI_tags[df_PHI_tags["Tag"].isin(missing_tags)]
missing_tags_df = missing_tags_df.copy() # since missing_tags was a slice, copy

print("ALERT: the following values are in the PHI Table E but not in the allTags table and have NOT been anonymized. Please check and add manually if necessary")
for index, row in missing_tags_df.iterrows():
    print(f"Tag: {row['Tag']}, Attribute: {row['Attribute Name']}")

# ADD VR COLUMN FOR THESE, SINCE THEY DO NOT EXIST IN THE ALLTAGS TABLE
missing_tags_df.loc[:,"VR"] = "FILL IN"
missing_tags_df.loc[:,"Name"] =  missing_tags_df.loc[:,"Attribute Name"] # make name column based on "Attribute Name" to merge with allTags dataframe


missing_tags_df.loc[missing_tags_df["Attribute Name"].str.contains("UID"),'VR'] = "UI"
# note VR = PRIVATETAGS is not an official DICOM VR but we will fill it with "PRIVATETAGS" to specify the correct anon later
missing_tags_df.loc[missing_tags_df["Tag"] == "(gggg,eeee) where gggg is odd", 'VR'] = "PRIVATETAGS"
missing_tags_df.loc[missing_tags_df["Tag"] == "(50xx,xxxx)", 'VR'] = "will be removed because code X"
# (50xx,xxxx) is X type, can be removed so do not need VR
# xxx is wildcard in XNAT

missing_tags_df.drop(["Attribute Name", "Retd. (from PS3.6 )","In Std. Comp. IOD (from PS3.3 )"], axis=1) 

print(missing_tags_df)

# filter df with all tags and descriptions and VR to only include those in the df_PHI_tags
# we need to combine both since the original df has the VR values and the PHI df does not
df_filtered = df[df["Tag"].isin(df_PHI_tags["Tag"])]


# Merge the filtered table1 with table2 on the specified column
# inner specifies to use only tags in both dataframes
df_anon = pd.merge(df_filtered, df_PHI_tags, on="Tag", how='inner')
print(df_anon.head(10))

# now add the tags from df_PHI_tags to the df_anon dataframe


df_anon= pd.concat([df_anon, missing_tags_df], ignore_index=True)

df_anon.drop(["Attribute Name", "Keyword", "Retd. (from PS3.6 )","In Std. Comp. IOD (from PS3.3 )", "VM", "Unnamed: 5"], axis=1) 

print("printing concatenated")
print(df_anon.head(10))



# create anonymisation column
df_anon.loc[:,"Anonymisation"] = "TBD"

# define replacement anonymisation data type based on VR type
AE_Anon = "\"ANON\""
AS_Anon = "\"000Y\""
CS_Anon = "\"ANON\""
DA_Anon = "\"00000000\""
DT_Anon = "\"00000000000000.000000\""
IS_Anon = "\"0000\""
LO_Anon = "\"ANON\""
LT_Anon = "\"ANON\""
PN_Anon = "\"ANON\""
SH_Anon = "\"ANON\""
ST_Anon = "\"ANON\""
TM_Anon = "\"000000.000000\""
UT_Anon = "\"ANON\"" # UT means unlimited text
UC_Anon = "\"ANON\"" # UC means unlimited characters
UR_Anon = "\"https://thisisaplaceholderlink.com\""
UN_Anon = "\"ANON\"" # UN is unknown, apparently flexible data type so replace with string 


#TODO need to add anonymisation for SQ and OB. It is not straightforward, e.g. for SQ which can have nested elements that need to be strings, numbers, dates etc


def replaceTagifExists(AnonType):
    return df_anon["Tag"].astype(str) + f" ?= {AnonType}"

def hashUID():
    return df_anon["Tag"].astype(str) + " ?= hashUID[" + df_anon["Tag"].astype(str) + "]"

def removeTag():
    return "-" + df_anon["Tag"].astype(str)


df_anon.loc[df_anon['VR'] == 'PRIVATETAGS', 'Anonymisation'] = f"removeAllPrivateTags"
df_anon.loc[(df_anon['VR'] == 'AE') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(AE_Anon)
df_anon.loc[(df_anon['VR'] == 'AS') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(AS_Anon)
df_anon.loc[(df_anon['VR'] == 'CS') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(CS_Anon)
df_anon.loc[(df_anon['VR'] == 'DA') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(DA_Anon)
df_anon.loc[(df_anon['VR'] == 'DS') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = hashUID()
# TODO check if this is an issue because maybe hashUID exceeds 16 characters?
df_anon.loc[(df_anon['VR'] == 'DT') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(DT_Anon)
df_anon.loc[(df_anon['VR'] == 'IS') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(IS_Anon)
df_anon.loc[(df_anon['VR'] == 'LO') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(LO_Anon)
df_anon.loc[(df_anon['VR'] == 'LT') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(LT_Anon)
#df_anon.loc[df_anon['VR'] == 'OB', 'Anonymisation'] = f" ?= {OB_Anon}" TODO check
# # NOTE OB CAN BE VARIOUS DATA TYPES BUT ALL OB IN THESE TABLES ARE ALSO TYPE X SO WILL BE REMOVED
df_anon.loc[(df_anon['VR'] == 'PN') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(PN_Anon)
df_anon.loc[(df_anon['VR'] == 'SH') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(SH_Anon)
df_anon.loc[(df_anon['VR'] == 'ST') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(ST_Anon)
df_anon.loc[(df_anon['VR'] == 'TM') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(TM_Anon)
df_anon.loc[(df_anon['VR'] == 'UC') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(UC_Anon)
df_anon.loc[(df_anon['VR'] == 'UR') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(UR_Anon)
df_anon.loc[(df_anon['VR'] == 'UT') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(UT_Anon)
df_anon.loc[(df_anon['VR'] == 'UN') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = replaceTagifExists(UN_Anon)

# type UI 
# should be unique but need to ensure even number is created with HashUID
df_anon.loc[(df_anon['VR'] == 'UI') & (df_anon['Basic Prof.'] != 'X'), 'Anonymisation'] = hashUID() # CHECK THIS DATA TYPE

#df_anon.loc[df_anon['VR'] == 'UL', 'Anonymisation'] = f" ?= {UL_Anon}" # NOTE IN THESE TABLES NO UL TAGS EXIST but check abyway


# check if VR = PRIVATETAGS, in this case we do not want to remove the individual tag ID but instead use removeAllPrivateTags
df_anon.loc[df_anon["VR"] == "PRIVATETAGS",'Anonymisation'] = "removeAllPrivateTags"

# For rows where "VR" is not "PRIVATETAGS" and 'Basic Prof.' is 'X', remove tag 
# (X indicates such tags can be removed according to this indicates the field can be removed: 
# source: https://dicom.nema.org/medical/dicom/current/output/chtml/part15/chapter_E.html)

df_anon.loc[(df_anon["VR"] != "PRIVATETAGS") & (df_anon['Basic Prof.'] == 'X'),'Anonymisation'] = removeTag()

print(df_anon.head(10))

# # # Create and Export the XNAT anonymisation code # # # 

# add name to XNAT code for annotating
df_anon.loc[:,"XNAT Code"] = df_anon["Anonymisation"].astype(str) + " //" + df_anon["Name"].astype(str)

# TODO
# double check for any cases where the anonymisation contains TBD (which would result from not specifying anonymisation )
# check to make sure that they are all type X so will be removed, if not print alert

# condition = ((df_anon["VR"] == "OB") | (df_anon["VR"] == "UL")) & (df_anon['Basic Prof.'] != 'X')
problematicTags= df_anon["Anonymisation"].str.contains("TBD") 

# Create a set to store VRs for which we still need to define anonymisation
unique_vr_values = set()

for index, row in df_anon[problematicTags].iterrows():
    print(f"ALERT: The tag {row['Tag']} with the name {row['Name']} is VR {row['VR']} and needs to be anonymized!")
    # Add VR value to the set
    unique_vr_values.add(row["VR"])

# Convert the set to a list if needed
unsolved_vr_list = list(unique_vr_values)
print("Unique VR values that still need replacement method and are not automatically removed (not X):", unsolved_vr_list)


# # # Create and Export the XNAT anonymisation code # # # 

# add name to XNAT code for annotating
df_anon.loc[:,"XNAT Code"] = df_anon["Anonymisation"].astype(str) + " //" + df_anon["Name"].astype(str)

# save dataframe of the PHI with the VR (ie our anon dataframe including VR and Basic Prof. type) for reference
df_anon.to_csv(os.path.join(myFolder, "dataframe_PHI_with_VR.txt"), index=False, quoting = csv.QUOTE_NONE, sep="\t")

# replace header name "XNAT Code" with version, export XNAT code column as .txt file
#NOTE this will not work (will still have "TBD") if unresolved_vr_list if there are ANY problematicTags (ie those where VR type has not been designated a replacement)

df_anon = df_anon.rename(columns={"XNAT Code": 'Version \"6.5\"'})
# optionally export the dataframe that has SQand OB identieid with "TBD"
# df_anon["Version \"6.5\""].to_csv(os.path.join(myFolder, "XNAT_code_with_undetermined.txt"), index=False, quoting = csv.QUOTE_NONE, sep="\t")

# now export version WITHOUT VR values that are not anonymised yet to test anonymisation of all other VR types

# Join the values into a single regular expression string with the OR (|) operator
unresolvedVRTypes = "|".join(unsolved_vr_list)

# exclude OB and SQ types for now, to make an incomplete script to test other anonymisations
df_anon_INCOMPLETE = df_anon[~df_anon["VR"].str.contains(unresolvedVRTypes, na=False)]


df_anon_INCOMPLETE["Version \"6.5\""].to_csv(os.path.join(myFolder, "XNAT_code_incomplete.txt"), index=False, quoting = csv.QUOTE_NONE, sep="\t")              

