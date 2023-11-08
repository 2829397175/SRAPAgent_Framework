chcp 65001

@REM for /l %%i in (1,1,3) do (
@REM     python main.py --task "PHA_5tenant_3community_19house_ver1_nofilter_hightem" >> test.log
@REM     echo This is the %%i loop 
@REM )

@REM task_list = (
@REM     "PHA_51tenant_5community_28house_ver1_nofilter_multilist",
@REM     "PHA_51tenant_5community_28house_ver1_nofilter_multilist_priority",
@REM     "PHA_51tenant_5community_28house_ver1_nofilter_multilist_priority_7t_5h",
@REM     "PHA_51tenant_5community_28house_ver1_nofilter_singlelist",
@REM     "PHA_51tenant_5community_28house_ver1_nofilter_singlelist_priority",
@REM     "PHA_51tenant_5community_28house_ver2_nofilter_multilist_priority_7t_5h"
@REM )

task_list = (
    "PHA_51tenant_5community_28house_ver1_nofilter_multilist_priority_7t_5h",
    "PHA_51tenant_5community_28house_ver1_nofilter_singlelist",
    "PHA_51tenant_5community_28house_ver2_nofilter_multilist_priority_7t_5h"
)

api_path = "LLM_PublicHouseAllocation\llms\api_aiguoguo.json"

for task_name in "${task_list[@]}"
do
    python main.py --task "$task_name" --api_path "$api_path"  --clear_cache>> "$task_name".log
done