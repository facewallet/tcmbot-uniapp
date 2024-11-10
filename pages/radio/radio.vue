<template>
  <view class="container">
    <form @submit="handleSubmit">
      <view v-for="field in dialogue.formList" :key="field.id" class="form-group">
        <view class="label">{{ field.label }}</view>
        <input v-if="field.type === 'text'" :placeholder="field.placeholder" v-model="field.value" type="text" :name="field.label" class="input-text" :required="field.required === 'true'" />
        <input v-if="field.type === 'password'" :placeholder="field.placeholder" v-model="field.value" type="password" :name="field.label" class="input-password" :required="field.required === 'true'" />
        <radio-group v-if="field.type === 'radio'" class="radio-group" @change="value => handleRadioChange(value, field)">
          <label v-for="option in field.options" :key="option.id" class="radio-label">
            <radio :value="option.value" :checked="field.value === option.value" class="radio-input" />
            <view v-if="option.type === 'button'">
              <button @click="handleButtonClick(option.value)" class="button">{{ option.label }}</button>
            </view>
            <view v-else-if="option.type === 'text'">
              <input :placeholder="option.placeholder" v-model="option.value" type="text" class="input-text" />
            </view>
            <view v-else>
              <text class="radio-text">{{ option.label }}</text>
            </view>
          </label>
        </radio-group>
        <checkbox-group v-if="field.type === 'checkbox'" class="checkbox-group" @change="value => handleCheckboxChange(value, field)">
          <label v-for="option in field.options" :key="option.id" class="checkbox-label">
            <checkbox :value="option.value" :checked="field.values && field.values.includes(option.value)" class="checkbox-input" />
            <text class="checkbox-text">{{ option.label }}</text>
          </label>
        </checkbox-group>
        <view v-if="field.type === 'file'">
          <input type="file" @change="event => handleFileChange(event, field)" :name="field.label" class="input-file" :required="field.required === 'true'" />
        </view>
      </view>
      <button form-type="submit" class="submit-button">提交</button>
    </form>
  </view>
</template>

<script>
export default {
  data() {
    return {
      dialogue: {
        formList: []
      }
    };
  },
  created() {
    this.fetchDialogue();
  },
  methods: {
    fetchDialogue() {
      uni.request({
        url: '/api/pub/dialogue',
        success: (res) => {
          if (res.data && res.data.type === 'form') {
            this.dialogue = res.data;
          }
        },
        fail: (err) => {
          console.error('Failed to fetch dialogue:', err);
        }
      });
    },
    handleRadioChange(value, field) {
      field.value = value.detail.value;
    },
    handleCheckboxChange(value, field) {
      field.values = value.detail.value;
    },
    handleFileChange(event, field) {
      const file = event.target.files[0];
      field.value = file;
    },
    handleButtonClick(value) {
      // Handle button click event
      console.log('Button clicked:', value);
    },
    handleSubmit(event) {
      event.preventDefault();
      const formData = new FormData();
      this.dialogue.formList.forEach(field => {
        if (field.type === 'file') {
          formData.append(field.label, field.value);
        } else {
          formData.append(field.label, field.value || '');
        }
      });
      uni.request({
        url: '/api/pub/dialogue',
        method: 'POST',
        data: JSON.stringify(this.dialogue),
        header: {
          'Content-Type': 'application/json'
        },
        success: (res) => {
          console.log('Form submitted successfully:', res);
        },
        fail: (err) => {
          console.error('Failed to submit form:', err);
        }
      });
    }
  }
};
</script>

<style>
.container {
  padding: 20px;
}
.form-group {
  margin-bottom: 20px;
}
.label {
  display: block;
  margin-bottom: 5px;
}
.input-text,
.input-password,
.input-file {
  width: 100%;
  padding: 10px;
  margin-top: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.radio-group,
.checkbox-group {
  display: flex;
  flex-wrap: wrap;
}
.radio-label,
.checkbox-label {
  display: flex;
  align-items: center;
  margin-right: 20px;
  margin-bottom: 10px;
}
.radio-input,
.checkbox-input {
  margin-right: 5px;
}
.radio-text,
.checkbox-text {
  margin-left: 5px;
}
.submit-button {
  width: 100%;
  padding: 10px;
  background-color: #007aff;
  color: #fff;
  border: none;
  border-radius: 4px;
}
</style>