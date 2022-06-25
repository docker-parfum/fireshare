import React from 'react'
import { Box, Grid, Paper, Stack, Typography } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import styled from '@emotion/styled'
import { VideoService } from '../../services'
import { getSetting } from '../../common/utils'

const Input = styled('input')({
  display: 'none',
})

const uiConfig = getSetting('ui_config')

const UploadCard = ({ authenticated, feedView = false, publicUpload = false, cardWidth, handleAlert }) => {
  const cardHeight = cardWidth / 1.77 + 32
  const [selectedFile, setSelectedFile] = React.useState()
  const [isSelected, setIsSelected] = React.useState(false)
  const [progress, setProgress] = React.useState(0)

  const changeHandler = (event) => {
    setSelectedFile(event.target.files[0])
    setIsSelected(true)
  }

  const uploadProgress = (progress) => setProgress(progress)

  React.useEffect(() => {
    async function upload() {
      const formData = new FormData()
      formData.append('file', selectedFile)
      try {
        if (publicUpload) {
          await VideoService.publicUpload(formData, uploadProgress)
        }
        if (!publicUpload && authenticated) {
          await VideoService.upload(formData, uploadProgress)
        }
        handleAlert({ type: 'success', message: "You're upload will be available after the next scan.", open: true })
      } catch (err) {
        handleAlert({
          type: 'error',
          message: `An error occurred while uploading your video.`,
          open: true,
        })
      }
      VideoService.scan().catch((err) => console.error(err))
      setProgress(0)
      setIsSelected(false)
    }
    if (selectedFile) upload()
    // eslint-disable-next-line
  }, [selectedFile])

  if (feedView && !uiConfig?.show_public_upload) return null
  if (!feedView && !uiConfig?.show_admin_upload) return null

  return (
    <Grid item sx={{ ml: 0.75, mr: 0.75, mb: 1.5 }}>
      <label htmlFor="icon-button-file">
        <Paper
          sx={{
            width: cardWidth,
            height: cardHeight,
            cursor: 'pointer',
            background: 'rgba(0,0,0,0)',
          }}
          variant="outlined"
        >
          <Box
            sx={{
              position: 'absolute',
              zIndex: 1,
              height: cardHeight,
              width: cardWidth * progress,
              backgroundImage: 'linear-gradient(140deg, #BC00E6DF, #FF3729D9)',
              borderRadius: '10px',
            }}
          />
          <Box sx={{ display: 'flex', p: 2, height: '100%' }} justifyContent="center" alignItems="center">
            <Stack sx={{ zIndex: 2, width: '100%' }} alignItems="center">
              {!isSelected && (
                <Input
                  id="icon-button-file"
                  accept="video/mp4,video/webm,video/mov"
                  type="file"
                  name="file"
                  onChange={changeHandler}
                />
              )}
              <CloudUploadIcon sx={{ fontSize: 75 }} />
              {progress !== 0 && progress !== 1 && (
                <Typography variant="overline" align="center" sx={{ fontWeight: 600, fontSize: 16 }}>
                  Uploading... {(100 * progress).toFixed(0)}%
                </Typography>
              )}
              {progress === 1 && (
                <Typography variant="overline" align="center" sx={{ fontWeight: 600, fontSize: 16 }}>
                  Processing...
                </Typography>
              )}
            </Stack>
          </Box>
        </Paper>
      </label>
    </Grid>
  )
}

export default UploadCard