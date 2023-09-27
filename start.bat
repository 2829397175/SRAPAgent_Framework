chcp 65001

for /l %%i in (1,1,3) do (
    python main.py --task "PHA_5tenant_3community_19house_ver1_nofilter_hightem" >> test.log
    echo This is the %%i loop 
)