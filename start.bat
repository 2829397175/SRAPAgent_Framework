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


SETLOCAL ENABLEDELAYEDEXPANSION

SET api_path=LLM_PublicHouseAllocation\llms\api.json
SET task_list="PHA_51tenant_5community_28house_ver1_nofilter_singlelist" "PHA_51tenant_5community_28house_ver2_nofilter_multilist_priority_7t_5h"

FOR %%A IN (%task_list%) DO (
    python main.py --task %%A --api_path %api_path% --clear_cache >> "%%A.log"
    echo This is the %%A loop 
)

ENDLOCAL