package vip.easystudy.tcm.domain;

import lombok.Data;

import java.util.Date;
import java.util.List;
@Data
public class Dialogue {
    private Long id;
    private Long parent_id;
    private Long last_id;
    private String uuid;
    private Long window_id;
    private Long sub_window_id;
    private String need_sub_window;
    private String sub_window_status;
    private Long session_id;
    private Long user_id;
    private String user_uuid;
    private String user_name;
    private String user_avatar;
    private String speaker;
    private String category;
    private Integer number;
    private String type;
    private String content;
    private String url;
    private String modal;
    private String json;
    private String status;
    private Long tenant_id;
    private String tenant_name;
    private String appid;
    private Long channel_id;
    private String channel_name;
    private String round;
    private String trace_id;
    private Long downstream_id;
    private Integer token;
    private String user_intent;
    private String bot_intent;
    private String source;
    private String platform;
    private Long creator_id;
    private String creator_name;
    private Long updater_id;
    private String updater_name;
    private Date create_date;
    private Date update_date;
    private List<DialogueForm> formList;
}



