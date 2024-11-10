package vip.easystudy.tcm.domain;

import lombok.Data;

import java.util.Date;
import java.util.List;

@Data
public class DialogueForm {
    private Long id;
    private Long parent_id;
    private Long dialogue_id;
    private Long session_id;
    private Long slot_id;
    private String placeholder;
    private String label;
    private String type;
    private String value;
    private List<String> values;
    private String disabled;
    private String required;
    private String status;
    private Integer weight;
    private Integer version;
    private String remark;
    private Long tenant_id;
    private String tenant_name;
    private String appid;
    private Long creator_id;
    private Long updater_id;
    private String creator_name;
    private String updater_name;
    private Date create_date;
    private Date update_date;
    
    private List<DialogueForm> options;
}
