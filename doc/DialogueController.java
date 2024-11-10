package vip.easystudy.tcm.controller;


import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import vip.easystudy.tcm.domain.Dialogue;
import vip.easystudy.tcm.domain.DialogueForm;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@RestController
@RequestMapping("/pub")
public class DialogueController {

    @GetMapping("/dialogue")
    public ResponseEntity<Dialogue> getDialogue() {
        Dialogue dialogue = new Dialogue();
        dialogue.setType("form");
        dialogue.setFormList(createDialogueForms());
        return ResponseEntity.ok(dialogue);
    }

    @PostMapping("/dialogue")
    public ResponseEntity<Dialogue> postDialogue(@RequestBody Dialogue dialogue) {
        // Here you would handle the form submission, e.g., save to database
        // For now, we just return the submitted dialogue
        System.out.println("suansuan");
        System.out.println(dialogue);
        return ResponseEntity.ok(dialogue);
    }

    private List<DialogueForm> createDialogueForms() {
        List<DialogueForm> forms = new ArrayList<>();

        // Name input
        DialogueForm nameInput = new DialogueForm();
        nameInput.setId(1L);
        nameInput.setLabel("姓名");
        nameInput.setPlaceholder("请输入姓名");
        nameInput.setType("text");
        nameInput.setRequired("true");
        nameInput.setValue("如意");
        forms.add(nameInput);

        // Password input
        DialogueForm passwordInput = new DialogueForm();
        passwordInput.setId(2L);
        passwordInput.setLabel("密码");
        passwordInput.setPlaceholder("请输入密码");
        passwordInput.setType("password");
        passwordInput.setRequired("true");
        forms.add(passwordInput);

        // Gender radio
//        DialogueForm genderRadio = new DialogueForm();
//        genderRadio.setId(3L);
//        genderRadio.setLabel("性别");
//        genderRadio.setType("radio");
//        genderRadio.setValue("male");
//        List<DialogueForm> genderOptions = new ArrayList<>();
//        DialogueForm maleOption = new DialogueForm();
//        maleOption.setId(31L);
//        maleOption.setLabel("男");
//        maleOption.setValue("male");
//        genderOptions.add(maleOption);
//        DialogueForm femaleOption = new DialogueForm();
//        femaleOption.setId(32L);
//        femaleOption.setLabel("女");
//        femaleOption.setValue("female");
//        genderOptions.add(femaleOption);
//        genderRadio.setOptions(genderOptions);
//        forms.add(genderRadio);

        DialogueForm radios = new DialogueForm();
        radios.setId(3L);
        radios.setLabel("请选择");
        radios.setType("radio");
        List<DialogueForm> genderOptions = new ArrayList<>();
        DialogueForm option01 = new DialogueForm();
        option01.setId(31L);
        option01.setLabel("挂号");
        option01.setValue("register");
        option01.setType("button");
        genderOptions.add(option01);
        DialogueForm option02 = new DialogueForm();
        option02.setId(32L);
        option02.setLabel("提交结果");
        option02.setPlaceholder("请提交结果");
        option02.setType("text");
        genderOptions.add(option02);
        radios.setOptions(genderOptions);
        forms.add(radios);

        // Hobbies checkbox
        DialogueForm hobbiesCheckbox = new DialogueForm();
        hobbiesCheckbox.setId(4L);
        hobbiesCheckbox.setLabel("兴趣爱好");
        hobbiesCheckbox.setType("checkbox");
        List<String> stringList = new ArrayList<String>();
        stringList.add("sport");
        hobbiesCheckbox.setValues(stringList);
        List<DialogueForm> hobbiesOptions = new ArrayList<>();
        DialogueForm sportOption = new DialogueForm();
        sportOption.setId(41L);
        sportOption.setLabel("运动");
        sportOption.setValue("sport");
        hobbiesOptions.add(sportOption);
        DialogueForm readingOption = new DialogueForm();
        readingOption.setId(42L);
        readingOption.setLabel("阅读");
        readingOption.setValue("reading");
        hobbiesOptions.add(readingOption);
        hobbiesCheckbox.setOptions(hobbiesOptions);
        forms.add(hobbiesCheckbox);

        // File upload
        DialogueForm fileUpload = new DialogueForm();
        fileUpload.setId(5L);
        fileUpload.setLabel("文件上传");
        fileUpload.setType("file");
        forms.add(fileUpload);

        return forms;
    }
}

