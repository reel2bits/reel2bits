// File imported from https://git.pleroma.social/pleroma/pleroma-fe/tree/develop/src/components/image_cropper

<template>
  <div class="image-cropper">
    <div v-if="dataUrl">
      <div class="image-cropper-image-container">
        <img
          ref="img"
          :src="dataUrl"
          alt=""
          @load.stop="createCropper"
        >
      </div>
      <div class="image-cropper-buttons-wrapper">
        <b-button
          :disabled="submitting"
          @click="submit()"
          v-text="saveText"
          variant="primary"
        />
        <b-button
          :disabled="submitting"
          @click="destroy"
          v-text="cancelText"
          variant="link"
        />
        <!--<b-button
          :disabled="submitting"
          @click="submit(false)"
          v-text="saveWithoutCroppingText"
        />-->
        <i
          v-if="submitting"
          class="icon-spin4 animate-spin"
        />
      </div>
      <div
        v-if="submitError"
        class="alert error"
      >
        {{ submitErrorMsg }}
        <i
          class="button-icon icon-cancel"
          @click="clearError"
        />
      </div>
    </div>
    <input
      ref="input"
      type="file"
      class="image-cropper-img-input"
      :accept="mimes"
    >
  </div>
</template>

<style lang="scss">
.image-cropper {
  &-img-input {
    display: none;
  }

  &-image-container {
    position: relative;

    img {
      display: block;
      max-width: 100%;
    }
  }

  &-buttons-wrapper {
    margin-top: 10px;

    button {
      margin-top: 5px;
    }
  }
}
</style>

<script>
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'

const ImageCropper = {
  props: {
    trigger: {
      type: [String, window.Element],
      required: true
    },
    submitHandler: {
      type: Function,
      required: true
    },
    cropperOptions: {
      type: Object,
      default () {
        return {
          aspectRatio: 1,
          autoCropArea: 1,
          viewMode: 1,
          movable: false,
          zoomable: false,
          guides: false
        }
      }
    },
    mimes: {
      type: String,
      default: 'image/png, image/gif, image/jpeg'
    },
    saveButtonLabel: {
      type: String
    },
    saveWithoutCroppingButtonlabel: {
      type: String
    },
    cancelButtonLabel: {
      type: String
    }
  },
  data () {
    return {
      cropper: undefined,
      dataUrl: undefined,
      filename: undefined,
      submitting: false,
      submitError: null
    }
  },
  computed: {
    saveText () {
      return this.saveButtonLabel || this.$pgettext('Content/ImageCropper/Button/Label', 'Save')
    },
    saveWithoutCroppingText () {
      return this.saveWithoutCroppingButtonlabel || this.$pgettext('Content/ImageCropper/Button/Label', 'Save without cropping')
    },
    cancelText () {
      return this.cancelButtonLabel || this.$pgettext('Content/ImageCropper/Button/Label', 'Cancel')
    },
    submitErrorMsg () {
      return this.submitError && this.submitError instanceof Error ? this.submitError.toString() : this.submitError
    }
  },
  methods: {
    destroy () {
      if (this.cropper) {
        this.cropper.destroy()
      }
      this.$refs.input.value = ''
      this.dataUrl = undefined
      this.$emit('close')
    },
    submit (cropping = true) {
      this.submitting = true
      this.avatarUploadError = null
      this.submitHandler(cropping && this.cropper, this.file)
        .then(() => this.destroy())
        .catch((err) => {
          this.submitError = err
        })
        .finally(() => {
          this.submitting = false
        })
    },
    pickImage () {
      this.$refs.input.click()
    },
    createCropper () {
      this.cropper = new Cropper(this.$refs.img, this.cropperOptions)
    },
    getTriggerDOM () {
      return typeof this.trigger === 'object' ? this.trigger : document.querySelector(this.trigger)
    },
    readFile () {
      const fileInput = this.$refs.input
      if (fileInput.files != null && fileInput.files[0] != null) {
        this.file = fileInput.files[0]
        let reader = new window.FileReader()
        reader.onload = (e) => {
          this.dataUrl = e.target.result
          this.$emit('open')
        }
        reader.readAsDataURL(this.file)
        this.$emit('changed', this.file, reader)
      }
    },
    clearError () {
      this.submitError = null
    }
  },
  mounted () {
    // listen for click event on trigger
    const trigger = this.getTriggerDOM()
    if (!trigger) {
      this.$emit('error', 'No image make trigger found.', 'user')
    } else {
      trigger.addEventListener('click', this.pickImage)
    }
    // listen for input file changes
    const fileInput = this.$refs.input
    fileInput.addEventListener('change', this.readFile)
  },
  beforeDestroy: function () {
    // remove the event listeners
    const trigger = this.getTriggerDOM()
    if (trigger) {
      trigger.removeEventListener('click', this.pickImage)
    }
    const fileInput = this.$refs.input
    fileInput.removeEventListener('change', this.readFile)
  }
}

export default ImageCropper
</script>
