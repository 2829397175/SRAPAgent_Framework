# Log Structure


ver1 政策：

假设系统最多可以运行3轮(max_turn)

- round_id : 系统运行的轮数 (environment.cnt_turn)
    - log_round: 发给前端的选择信息
        - tenant_id： tenant_id 号 tenant的选择信息
    - log_round_prompts: xuan


- group:（若根据ht分队列）
    - tenant_id: 选队列时 （所有tenant都会有）
        - log_round: 选ht 时候的 发给前端的信息
        - log_round_prompts: 选ht 时候的 prompt和response

需要修改的ver2:
1. group里面的 prompts
2. filter后的house 存在过多的问题

- round_id : 系统运行的轮数 (environment.cnt_turn)
    - log_round: 发给前端的选择信息
        - tenant_id： tenant_id 号 tenant的选择信息
    - log_round_prompts: 选房过程的prompt和response
        - tenant_id： tenant_id 号 tenant的 选房过程 c,ht,h prompt，response

    - log_social_network:
        - 这个轮内， 第几次social的 index （这个会重复c_num）
            - step_type:(在交流的步骤名) 【debug时候运行的顺序】

        - social_network_mem: 【context相关】
            - tenant_id A:
                - mail (还没发的信息)
                - social_network(邻接表)
                    - tenant_id B:
                        - dialogues (A->B B->A) list存
                            - message
                        - chat_history （dialogues summary）
                        - relation
                        - comment


