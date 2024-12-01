import copy

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from dss.dao.dialogue_dao import DecisionDialogueDAO
from dss.dao.dialogue_form_dao import DecisionDialogueFormDAO
from dss.dao.edge import DecisionEdgeDAO
from dss.dao.node import DecisionNodeDAO
from dss.dao.node_slot import DecisionNodeSlotDAO
from dss.dao.slot_mapping import DecisionSlotMappingDAO
from dss.dao.tree import DecisionTreeDAO
from dss.dao.user_slot import DecisionUserSlotDAO
from dss.domain.dialogue import Dialogue, dialogue_2_decision_dialogue
from dss.domain.dialogue_form import dialogue_form_2_decision_dialogue_form, DialogueForm
from dss.domain.message import Message
from dss.service.slot_service import SlotService
from dss.service.intent_service import IntentService
from dss.service.similarity_service import do_slot_similarity
from dss.util.medical_embedding_util import do_embedding_4_user_slot_list
from dss.util.snowflake_util import SnowflakeIdWorker

app = FastAPI()
# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许任何来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

TEXT = "text"
FORM = "form"
RADIO = "radio"
BOT = "bot"
USER = "user"
DIALOGUE = "dialogue"
DIALOGUELIST = "dialogueList"
DO_AGENT_SELECT = "do_agent_select"
FINISH_AGENT_SELECT = "finish_agent_select"
DO_EDGE_SELECT = "do_edge_select"
FINISH_EDGE_SELECT = "finish_edge_select"
DO_SLOT_FILL = "do_slot_fill"
FINISH_SLOT_FILL = "finish_slot_fill"
FINISH_SESSION = "finish_session"
USER_ASK = "user_ask"


# @app.get("/dss/slot/embedding")
# async def do_solt_embedding():
#     pass
# @app.get("/dss/build/node/slot")
# async def do_build_node_solt():
#     pass

@app.post("/dss/build")
async def do_build():
    # 1、构建树tree
    # 2.槽位提取提示词、构建节点node
    # 用户节点槽位映射表.SQL、构建节点槽位，先弄节点上的，然后做do_embedding
    # 4.测试用例、构建边
    # 5、构建边的槽位
    # 6、递归去构建节点槽位表，自上而下构建，遍历这些节点，找到这些节点的parent_id，继承，
    # 7、找到end_id是本node_id的边，如果这个边有槽位，继承过来，这个逻辑放到user_slot里面去
    pass

intentService = IntentService()
slotService = SlotService()
worker = SnowflakeIdWorker(worker_id=1, data_center_id=1)
@app.post("/dss/dialogue")
async def do_dialogue(dialogue: Dialogue):
    print(dialogue)
    success_message = Message().success()
    fail_message = Message().fail()
    clone_dialogue = copy.deepcopy(dialogue)
    clone_dialogue.speaker = BOT
    try:
        if dialogue.speaker == USER:
            if USER_ASK == dialogue.user_intent:
                # do_intent(),返回top3 tree_id ，参考介子推
                intent_dict = intentService.do_intent(dialogue.content)
                print(intent_dict)
                # intent_dict 格式 {1: 0.9999999827208779, 2: 0.7438317072368655}
                # todo 判断intent_dict是否为空，为空则返回失败，则返回fail_message
                # todo 如果不为空，则首先做do_slot_extract，得到user_slot_list，并将user_slot_list入库
                # todo 然后遍历intent_dict,拿到tree_id，调用tree_dao.get_by_id(tree_id)拿到node_slot_list_list
                # todo 然后调用do_slot_similarity返回相似度最高的节点
                # todo 判断intent_dict是否为空，为空则返回失败，则返回fail_message
                if not intent_dict:
                    return fail_message
                session_id = worker.get_id()
                # todo 如果不为空，则首先做do_slot_extract，得到user_slot_list，并将user_slot_list入库
                user_slot_list = slotService.do_slot_extract(dialogue.content, session_id)
                user_slot_list = do_embedding_4_user_slot_list(user_slot_list)
                userSlotDAO = DecisionUserSlotDAO()
                userSlotDAO.add_list(user_slot_list)
                # todo 然后遍历intent_dict,拿到tree_id，调用tree_dao.get_by_id(tree_id)拿到node_slot_list_list
                clone_dialogue.type = FORM
                clone_dialogue.bot_intent = DO_AGENT_SELECT
                clone_dialogue.session_id = session_id
                forms = []
                radio_form = DialogueForm()
                radio_form.id = session_id
                radio_form.label = "推荐如下智能体"
                radio_form.type = RADIO
                radio_options = []
                for intent_id, score in intent_dict.items():
                    tree_id = intent_id
                    treeDAO = DecisionTreeDAO()
                    current_tree = treeDAO.get_by_id(tree_id)
                    nodeSlotDAO = DecisionNodeSlotDAO()
                    node_slot_list_list = nodeSlotDAO.get_node_slots_by_tree_id(tree_id)
                    similarity_dict_result = do_slot_similarity(user_slot_list, node_slot_list_list)
                    # best_matching_node =similarity_dict_result["best_node_slot_list"][0]
                    node_id =similarity_dict_result["best_node_slot_list"][0].node_id
                    option = DialogueForm()
                    option.id = tree_id
                    option.label = current_tree.label
                    option.value = str(tree_id) + "-" + str(node_id)
                    radio_options.append(option)
                # do_agent_select  一个agent也让用户选择
                radio_form.options = radio_options
                forms.append(radio_form)
                clone_dialogue.forms = forms
                success_message.add_data("dialogue", clone_dialogue)
                return success_message
            elif DO_AGENT_SELECT == dialogue.bot_intent:
                session_id = dialogue.session_id
                forms = dialogue.forms
                dialogue_form = forms[0]
                string = dialogue_form.value
                array = string.split("-")
                tree_id = int(array[0])
                node_id = int(array[1])
                clone_dialogue.tree_id = tree_id
                clone_dialogue.node_id = node_id
                # todo 根据session_id，node_id和flag= node，node_slot_relation=have，required=YES的，调用
                flag = 'node'
                node_slot_relation = 'have'
                # required = 'YES'
                # required = required
                slotMappingDAO = DecisionSlotMappingDAO()
                # 调用条件查询方法
                results = slotMappingDAO.find_by_condition(
                    session_id=session_id,
                    node_id=node_id,
                    flag=flag,
                    node_slot_relation=node_slot_relation
                )

                # 判断结果是否为空
                if results:
                    # 如果结果不为空，遍历结果
                    clone_dialogue.type = FORM
                    clone_dialogue.bot_intent = DO_SLOT_FILL
                    forms = []
                    for result in results:
                        print(f"ID: {result.id}, Session ID: {result.session_id}, Node ID: {result.node_id}, "
                              f"Flag: {result.flag}, Node Slot Relation: {result.node_slot_relation}, Required: {result.required}")
                        if result.need_fill == 'YES' and result.fill_method == 'boolean':
                            radio_form = DialogueForm()
                            radio_form.id = result.node_slot_id  #这是挂的是槽位ID，是对槽位的填充
                            radio_form.label = result.boolean_label
                            radio_form.type = RADIO
                            radio_options = []
                            option_yes = DialogueForm()
                            # option_yes.id = tree_id
                            option_yes.label = result.boolean_yes_label
                            option_yes.value = result.boolean_yes_value
                            radio_options.append(option_yes)

                            option_no = DialogueForm()
                            # option_yes.id = tree_id
                            option_no.label = result.boolean_no_label
                            option_no.value = result.boolean_no_value
                            radio_options.append(option_no)

                            radio_form.options = radio_options
                            forms.append(radio_form)
                    clone_dialogue.forms = forms
                    if len(forms) == 0:
                        return fail_message
                    else:
                        success_message.add_data("dialogue", clone_dialogue)
                        return success_message

                else:
                    # 如果结果为空，调用do_infer
                    # do_infer()
                    # 这时候没有必须要填充的槽位，则首先判断
                    # todo 判断edge_list是否为空，如果为空则查询该调用node_dao类获取node信息，如果不为空则遍历edge_list
                    # todo 判断该节点是否有子节点，如果有则让用户选边，如果该节点就是叶子节点，则直接返回solution
                    # todo 如果有子节点，则调用do_edge_select
                    edgeDAO = DecisionEdgeDAO()
                    edge_list = edgeDAO.query_by_start_id(node_id)
                    if not edge_list:  # 判断edge_list是否为空
                        # 如果为空，则调用node_dao类获取node信息
                        node_dao = DecisionNodeDAO()
                        node_info = node_dao.get_by_id(node_id)
                        if node_info.solution:
                            # 处理node_info
                            print("Node info:", node_info)
                            clone_dialogue.type = TEXT
                            clone_dialogue.content = node_info.solution
                            clone_dialogue.bot_intent = FINISH_SESSION
                            success_message.add_data("dialogue", clone_dialogue)
                            return success_message

                    else:
                        forms = []
                        radio_form = DialogueForm()
                        radio_form.id = node_id
                        radio_form.label = "请您选择"
                        radio_form.type = RADIO
                        radio_options = []
                        # 如果不为空，则遍历edge_list
                        for edge in edge_list:
                            # 处理每个edge
                            print("Edge:", edge)
                            option = DialogueForm()
                            option.id = edge.id
                            option.label = edge.label
                            option.value = edge.id
                            radio_options.append(option)
                        # do_agent_select  一个agent也让用户选择
                        radio_form.options = radio_options
                        forms.append(radio_form)
                        clone_dialogue.forms = forms
                        clone_dialogue.bot_intent = DO_EDGE_SELECT
                        success_message.add_data("dialogue", clone_dialogue)
                        return success_message

                    pass
                # if "1-1" == dialogue_form.value:
                #     pass
                # elif "2.槽位提取提示词-1" == dialogue_form.value:
                #     clone_dialogue.type = FORM
                #     clone_dialogue.bot_intent = DO_SLOT_FILL
                #     forms = []
                #     input_form = DialogueForm()
                #     input_form.id = 132
                #     input_form.label = "核酸"
                #     input_form.placeholder = "请输入核酸结果"
                #     input_form.type = TEXT
                #     input_form.required = "true"
                #     forms.append(input_form)
                #     clone_dialogue.forms = forms
                #     success_message.add_data("dialogue", clone_dialogue)
                #     return success_message
            elif DO_SLOT_FILL == dialogue.bot_intent:
                forms = dialogue.forms
                # todo dialogue_form绑定的是slot_id，前面要绑定才行
                # todo 遍历，然后判断 dialogue_form.value是否一致，如果都一直，则 如果不一致，则
                dialogue_form = forms[0]
                if "阳性" == dialogue_form.value:
                    clone_dialogue.type = TEXT
                    clone_dialogue.content = "推荐使用大青龙汤或者清肺排毒汤"
                elif "2.槽位提取提示词-1" == dialogue_form.value:
                    clone_dialogue.type = TEXT
                    clone_dialogue.content = "核酸不符合，请按普通感冒治疗"
                success_message.add_data("dialogue", clone_dialogue)
                return success_message
            elif DO_EDGE_SELECT == dialogue.bot_intent:
                pass
        # decision_dialogue = dialogue_2_decision_dialogue(dialogue)
        # decision_dialogue_dao = DecisionDialogueDAO()
        # decision_dialogue_dao.add(decision_dialogue)
        # if dialogue.forms:
        #     for form in dialogue.forms:
        #         # 调用转换函数并将结果添加到数据库
        #         decision_dialogue_form = dialogue_form_2_decision_dialogue_form(form)
        #         decision_dialogue_form_dao = DecisionDialogueFormDAO()
        #         decision_dialogue_form_dao.add(decision_dialogue_form)
        #
        # dialogue.speaker = 'bot'
        # dialogue.content = '我是DSS'
        # message.add_data("dialogue",dialogue)
        else:
            return fail_message
        return success_message
    except Exception as e:
        print('do_dialogue报错', e)

        return fail_message

@app.get("/dss/echo")
async def echo():
    dialogue = Dialogue()
    dialogue_form = DialogueForm()
    dialogue.forms.append(dialogue_form)

    return dialogue
# 启动应用
if __name__ == "__main__":
    intentService.do_recall()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)